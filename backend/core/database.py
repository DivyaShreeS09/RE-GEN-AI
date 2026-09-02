import os
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Session

_DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./regen_runs.db")
_connect_args = {"check_same_thread": False} if _DB_URL.startswith("sqlite") else {}
engine = create_engine(_DB_URL, connect_args=_connect_args)


class Base(DeclarativeBase):
    pass


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    org_name            = Column(String(256), index=True, nullable=False)
    org_type            = Column(String(128), nullable=False)
    created_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    coverage_pct        = Column(Float, default=0.0)
    confidence_pct      = Column(Float, default=0.0)
    regen_score_before  = Column(Float, default=0.0)
    regen_score_after   = Column(Float, default=0.0)
    total_wasted_liters = Column(Float, default=0.0)
    total_wasted_kwh    = Column(Float, default=0.0)
    total_co2_saved_kg  = Column(Float, default=0.0)
    payload             = Column(Text, nullable=True)


Base.metadata.create_all(engine)


def save_run(
    org_name: str,
    org_type: str,
    coverage_pct: float,
    confidence_pct: float,
    regen_before: float,
    regen_after: float,
    wasted_liters: float,
    wasted_kwh: float,
    co2_kg: float,
    payload_dict: dict,
) -> int:
    row = AnalysisRun(
        org_name=org_name,
        org_type=org_type,
        coverage_pct=coverage_pct,
        confidence_pct=confidence_pct,
        regen_score_before=regen_before,
        regen_score_after=regen_after,
        total_wasted_liters=wasted_liters,
        total_wasted_kwh=wasted_kwh,
        total_co2_saved_kg=co2_kg,
        payload=json.dumps(payload_dict),
    )
    with Session(engine) as session:
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id


def get_history(org_name: str, limit: int = 20) -> list[dict]:
    with Session(engine) as session:
        rows = (
            session.query(AnalysisRun)
            .filter(AnalysisRun.org_name == org_name)
            .order_by(AnalysisRun.created_at.desc())
            .limit(limit)
            .all()
        )
    return [
        {
            "id":                   r.id,
            "org_name":             r.org_name,
            "org_type":             r.org_type,
            "created_at":           r.created_at.isoformat(),
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
