"""Run a local or explicitly authorized additive migration with python -m core.schema."""
from sqlalchemy import Column, Integer, select, inspect

from core.database import Base, engine, MissionInferenceBudget
from core import recovery, telemetry  # register persistent models

from core.execution_queue import ExecutionJob
EXECUTION_JOB_TABLE = ExecutionJob.__tablename__


class SchemaRevision(Base):
    __tablename__ = "regen_schema_revision"
    version = Column(Integer, primary_key=True)


def upgrade(target=engine):
    with target.begin() as connection:
        if target.dialect.name == "postgresql":
            from sqlalchemy import text
            connection.execute(text("SELECT pg_advisory_xact_lock(192731)"))
        SchemaRevision.__table__.create(connection, checkfirst=True)
        revision = connection.scalar(select(SchemaRevision.version))
        if revision is None:
            Base.metadata.create_all(connection)
            connection.execute(SchemaRevision.__table__.insert().values(version=3))
        elif revision in (1, 2):
            ExecutionJob.__table__.create(connection, checkfirst=True)
            MissionInferenceBudget.__table__.create(connection, checkfirst=True)
            connection.execute(SchemaRevision.__table__.update().where(SchemaRevision.version == revision).values(version=3))
        elif revision != 3:
            raise RuntimeError("Unsupported RE:GEN schema revision.")


def require_schema():
    with engine.connect() as connection:
        if not inspect(connection).has_table(SchemaRevision.__tablename__) or connection.scalar(select(SchemaRevision.version)) != 3 or not all(inspect(connection).has_table(t) for t in (EXECUTION_JOB_TABLE, MissionInferenceBudget.__tablename__)):
            raise RuntimeError("Run the approved database migration before startup.")


def import_postal(path):
    """Import operator-reviewed, reuse-permitted locality evidence without network access."""
    import csv
    from datetime import date
    from pydantic import BaseModel, ConfigDict
    from core.recovery import Name, Pin, PostalArea
    from sqlalchemy.orm import Session

    class ReviewedArea(BaseModel):
        model_config = ConfigDict(extra="forbid")
        pin: Pin
        locality: Name
        source_document: Name
        reuse_permission: Name
        reviewer: Name
        publication_date: date
        reviewed_date: date

    with path.open(encoding="utf-8-sig", newline="") as source, Session(engine) as db:
        for record in csv.DictReader(source):
            row = ReviewedArea.model_validate(record)
            if not row.publication_date <= row.reviewed_date <= date.today():
                raise ValueError("Invalid publication or review date.")
            db.merge(PostalArea(pin=row.pin, locality=row.locality, provenance=row.model_dump(
                mode="json", exclude={"pin", "locality"})))
        db.commit()


def expire_records(retention_days, *, apply=False):
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import delete, func
    from core.database import AccessAudit, AnalysisRun, RunOwner
    from core.telemetry import Observation
    from core.recovery import MaterialPhoto, Mission, ServiceOutcome
    if retention_days < 1:
        raise ValueError("A positive facility retention period is required.")
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    with engine.begin() as conn:
        # Leave legacy records without an assigned tenant under operator control.
        runs = select(AnalysisRun.id).join(RunOwner, RunOwner.run_id == AnalysisRun.id).where(AnalysisRun.created_at < cutoff)
        counts = {}
        for table, condition in [(Observation, Observation.timestamp < cutoff.isoformat()),
                                 (MaterialPhoto, MaterialPhoto.created_at < cutoff.isoformat()),
                                 (AccessAudit, AccessAudit.created_at < cutoff)]:
            counts[table.__tablename__] = conn.scalar(select(func.count()).select_from(table).where(condition))
            if apply:
                conn.execute(delete(table).where(condition))
        # Open allocations and in-progress missions require explicit operator resolution.
        ended = select(Mission.id, Mission.version, Mission.events, Mission.tenant, Mission.request_id).where(
            Mission.state.in_(["cancelled","verified","no_feasible_action","handover_confirmed","completed","failed","professional_review"]))
        counts["terminal_missions"] = 0
        for mid, version, events, tenant, request in conn.execute(ended):
            if not events or datetime.fromisoformat(events[-1]["at"]) >= cutoff:
                continue
            counts["terminal_missions"] += 1
            if apply:
                removed = conn.execute(delete(Mission).where(Mission.id == mid, Mission.version == version))
                if removed.rowcount:
                    conn.execute(delete(ExecutionJob).where(ExecutionJob.mission_id == mid, ExecutionJob.tenant == tenant))
                    conn.execute(delete(MissionInferenceBudget).where(MissionInferenceBudget.tenant == tenant,
                                                                      MissionInferenceBudget.request_id == request))
                    conn.execute(delete(ServiceOutcome).where(ServiceOutcome.mission_id == mid))
        counts["owned_runs"] = conn.scalar(select(func.count()).select_from(runs.subquery()))
        if apply:
            old_ids = list(conn.scalars(runs))
            for offset in range(0, len(old_ids), 500):
                ids = old_ids[offset:offset+500]
                conn.execute(delete(RunOwner).where(RunOwner.run_id.in_(ids)))
                conn.execute(delete(AnalysisRun).where(AnalysisRun.id.in_(ids)))
        return counts


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewed-postal-csv", type=Path)
    parser.add_argument("--retention-days", type=int)
    parser.add_argument("--apply-retention", action="store_true")
    args = parser.parse_args()
    upgrade()
    if args.retention_days is not None:
        print(expire_records(args.retention_days, apply=args.apply_retention))
    if args.reviewed_postal_csv:
        import_postal(args.reviewed_postal_csv)
