"""Persistent, tenant-scoped analysis execution queue."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    Column, String, Integer, UniqueConstraint,
    select, update, or_, and_,
)
from sqlalchemy.orm import Session

from core.database import Base, engine


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class ExecutionJob(Base):
    __tablename__ = "execution_jobs"
    __table_args__ = (
        UniqueConstraint("tenant", "mission_id"),
    )

    id = Column(String(36), primary_key=True)
    tenant = Column(String(128), nullable=False, index=True)
    mission_id = Column(String(36), nullable=False)
    subject = Column(String(256), nullable=False)
    status = Column(String(24), nullable=False, index=True)
    attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(String(40), nullable=False)
    updated_at = Column(String(40), nullable=False)
    lease_until = Column(String(40))
    claim_token = Column(String(36))
    error = Column(String(160))


@dataclass(frozen=True)
class InvestigationLease:
    tenant: str
    mission_id: str
    job_id: str
    token: str

    @property
    def subject(self):
        return "worker:" + self.job_id

    def guard(self, db):
        # This update and the mission checkpoint share a transaction and row lock.
        changed = db.execute(update(ExecutionJob).where(
            ExecutionJob.id == self.job_id, ExecutionJob.tenant == self.tenant,
            ExecutionJob.mission_id == self.mission_id, ExecutionJob.claim_token == self.token,
            ExecutionJob.status == "running", ExecutionJob.lease_until > timestamp(),
        ).values(updated_at=timestamp()))
        if changed.rowcount != 1:
            raise LostLease()


class LostLease(Exception):
    pass


def next_job():
    with Session(engine) as db:
        return db.execute(select(ExecutionJob.tenant, ExecutionJob.id).where(or_(
            ExecutionJob.status.in_(["queued","retry"]),
            and_(ExecutionJob.status == "running", ExecutionJob.lease_until <= timestamp())
        )).order_by(ExecutionJob.created_at).limit(1)).first()


def serialize(job):
    return {
        "id": job.id,
        "mission_id": job.mission_id,
        "status": job.status,
        "attempts": job.attempts,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "error": job.error,
    }


def enqueue(db, tenant, mission_id, subject):
    existing = db.scalar(select(ExecutionJob).where(
        ExecutionJob.tenant == tenant, ExecutionJob.mission_id == mission_id))
    if existing:
        return serialize(existing)
    job = ExecutionJob(id=str(uuid.uuid4()), tenant=tenant, mission_id=mission_id,
                       subject=subject, status="queued", attempts=0,
                       created_at=timestamp(), updated_at=timestamp())
    db.add(job)
    db.flush()
    return serialize(job)


def claim_job(tenant, identifier):
    current = timestamp()
    eligible = (
        ExecutionJob.id == identifier,
        ExecutionJob.tenant == tenant,
        or_(ExecutionJob.status.in_(["queued", "retry"]),
            and_(ExecutionJob.status == "running", ExecutionJob.lease_until <= current)),
    )
    token = str(uuid.uuid4())
    with Session(engine) as db:
        claimed = db.execute(update(ExecutionJob).where(*eligible, ExecutionJob.attempts < 3)
            .values(status="running", attempts=ExecutionJob.attempts + 1, claim_token=token,
                    updated_at=current, error=None,
                    lease_until=(datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat())
            .returning(ExecutionJob.mission_id, ExecutionJob.attempts)).first()
        if claimed is None:
            db.execute(update(ExecutionJob).where(*eligible, ExecutionJob.attempts >= 3)
                       .values(status="failed", lease_until=None, claim_token=None, updated_at=current,
                               error="Execution retry budget exhausted"))
        db.commit()
        if claimed:
            return {"id": identifier, "mission_id": claimed.mission_id,
                    "claim_token": token, "attempts": claimed.attempts}


def finish_job(tenant, identifier, token, status, error=None):
    if status not in ("completed", "retry", "failed", "paused"):
        raise ValueError("Invalid execution status")

    with Session(engine) as db:
        changed = db.execute(update(ExecutionJob).where(
            ExecutionJob.id == identifier,
            ExecutionJob.tenant == tenant,
            ExecutionJob.claim_token == token,
            ExecutionJob.lease_until > timestamp(),
            ExecutionJob.status == "running",
        ).values(
            status=status,
            error=error,
            updated_at=timestamp(),
            lease_until=None,
            claim_token=None,
        ))

        db.commit()
        return changed.rowcount == 1
