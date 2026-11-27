import os
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, null
from sqlalchemy.orm import DeclarativeBase, Session

_DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./regen_runs.db")
if os.getenv("REGEN_ENV") == "production" and not _DB_URL.startswith(("postgresql://", "postgresql+psycopg://")):
    raise RuntimeError("Production requires persistent PostgreSQL.")
if _DB_URL.startswith("postgresql://"):
    _DB_URL = _DB_URL.replace("postgresql://", "postgresql+psycopg://", 1)
_connect_args = {"check_same_thread": False, "autocommit": False} if _DB_URL.startswith("sqlite") else {}
_engine_options = {}
if _DB_URL.startswith("sqlite:") and os.getenv("REGEN_ENV") == "development" and os.getenv("REGEN_DEV_IDENTITY") == "1":
    from sqlalchemy.pool import NullPool
    _engine_options["poolclass"] = NullPool
engine = create_engine(_DB_URL, connect_args=_connect_args, hide_parameters=True, **_engine_options)


class Base(DeclarativeBase):
    pass


class MissionInferenceBudget(Base):
    __tablename__ = "mission_inference_budgets"
    tenant = Column(String(128), primary_key=True)
    request_id = Column(String(36), primary_key=True)
    charged = Column(Integer, nullable=False)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    org_name            = Column(String(256), index=True, nullable=False)
    org_type            = Column(String(128), nullable=False)
    created_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    coverage_pct        = Column(Float, default=0.0)
    confidence_pct      = Column(Float, nullable=True)
    regen_score_before  = Column(Float, default=0.0)
    regen_score_after   = Column(Float, default=0.0)
    total_wasted_liters = Column(Float, default=0.0)
    total_wasted_kwh    = Column(Float, default=0.0)
    total_co2_saved_kg  = Column(Float, default=0.0)
    payload             = Column(Text, nullable=True)


class RunOwner(Base):
    __tablename__ = "analysis_run_owners"
    run_id = Column(Integer, primary_key=True)
    tenant = Column(String(128), nullable=False, index=True)




class AccessAudit(Base):
    __tablename__ = "record_access_audit"
    id = Column(Integer, primary_key=True)
    tenant = Column(String(128), nullable=False, index=True)
    subject = Column(String(128), nullable=False)
    action = Column(String(32), nullable=False)
    run_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


def log_access(tenant, subject, action, run_id=None):
    with Session(engine) as session:
        session.add(AccessAudit(tenant=tenant, subject=subject, action=action, run_id=run_id))
        session.commit()


def delete_run(run_id, tenant, subject):
    with Session(engine) as session:
        owner = session.query(RunOwner).filter_by(run_id=run_id, tenant=tenant).one_or_none()
        if owner is None:
            return False
        session.query(AnalysisRun).filter_by(id=run_id).delete()
        session.delete(owner)
        session.add(AccessAudit(tenant=tenant, subject=subject, action="deleted", run_id=run_id))
        session.commit()
        return True


def save_run(
    org_name: str,
    org_type: str,
    coverage_pct: float,
    confidence_pct: float | None,
    regen_before: float,
    regen_after: float | None,
    wasted_liters: float,
    wasted_kwh: float,
    co2_kg: float | None,
    payload_dict: dict,
    *, tenant: str,
) -> int:
    row = AnalysisRun(
        org_name=org_name,
        org_type=org_type,
        coverage_pct=coverage_pct,
        confidence_pct=confidence_pct,
        regen_score_before=regen_before,
        regen_score_after=null() if regen_after is None else regen_after,
        total_wasted_liters=wasted_liters,
        total_wasted_kwh=wasted_kwh,
        total_co2_saved_kg=null() if co2_kg is None else co2_kg,
        payload=json.dumps(payload_dict),
    )
    with Session(engine) as session:
        session.add(row)
        session.flush()
        session.add(RunOwner(run_id=row.id, tenant=tenant))
        session.commit()
        session.refresh(row)
        return row.id


def get_run_by_id(analysis_id: int, *, tenant: str) -> dict | None:
    with Session(engine) as session:
        row = session.query(AnalysisRun).join(RunOwner, RunOwner.run_id == AnalysisRun.id).filter(
            AnalysisRun.id == analysis_id, RunOwner.tenant == tenant).one_or_none()
        if row is None:
            return None
    return {
        "id":                   row.id,
        "org_name":             row.org_name,
        "org_type":             row.org_type,
        "created_at":           row.created_at.replace(tzinfo=timezone.utc).isoformat(),
        "coverage_pct":         row.coverage_pct,
        "confidence_pct":       row.confidence_pct,
        "regen_score_before":   row.regen_score_before,
        "regen_score_after":    row.regen_score_after,
        "total_wasted_liters":  row.total_wasted_liters,
        "total_wasted_kwh":     row.total_wasted_kwh,
        "total_co2_saved_kg":   row.total_co2_saved_kg,
        "payload":              json.loads(row.payload) if row.payload else {},
    }


def get_history(org_name: str, limit: int = 20, *, tenant: str) -> list[dict]:
    with Session(engine) as session:
        rows = (
            session.query(AnalysisRun)
            .join(RunOwner, RunOwner.run_id == AnalysisRun.id)
            .filter(AnalysisRun.org_name == org_name, RunOwner.tenant == tenant)
            .order_by(AnalysisRun.created_at.desc())
            .limit(limit)
            .all()
        )
    return [
        {
            "id":                   r.id,
            "org_name":             r.org_name,
            "org_type":             r.org_type,
            "created_at":           r.created_at.replace(tzinfo=timezone.utc).isoformat(),
            "coverage_pct":         r.coverage_pct,
            "confidence_pct":       r.confidence_pct,
            "regen_score_before":   r.regen_score_before,
            "regen_score_after":    r.regen_score_after,
            "total_wasted_liters":  r.total_wasted_liters,
            "total_wasted_kwh":     r.total_wasted_kwh,
            "total_co2_saved_kg":   r.total_co2_saved_kg,
        }
        for r in rows
    ]
