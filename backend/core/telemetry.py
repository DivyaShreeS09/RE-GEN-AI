"""Authenticated, idempotent meter readings. Each series belongs to one instrumented zone."""
import csv
import hashlib
import secrets
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError
from datetime import datetime, timedelta
from typing import Literal
from statistics import median

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import AwareDatetime, Field
from sqlalchemy import JSON, Column, Float, Integer, String, UniqueConstraint, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.auth import Member, require_member
from core.database import Base, engine
from core.data_processor import UNIT_CONVERSION
from core.recovery import Input, Name, admin, now

router = APIRouter(tags=["Telemetry"])
UNITS = {"water_counter": "L", "energy_counter": "kWh", "power": "kW"}


class DeviceInput(Input):
    zone_id: Name
    metric: Literal["water_counter", "energy_counter", "power"]
    tariff_paise_per_unit: int | None = Field(default=None, ge=0, le=1000000)
    tariff_source: Name | None = None
    calibration_ref: Name
    calibration_due: AwareDatetime
    campus_id: Name | None = None
    building_id: Name | None = None
    floor_id: Name | None = None
    room_id: Name | None = None
    parent_device_id: str | None = Field(default=None, max_length=32)
    uncertainty_fraction: float = Field(default=0.05, ge=0, le=1)
    interval_seconds: int = Field(ge=1, le=86400)


class Device(Base):
    __tablename__ = "meter_devices"
    id = Column(String(32), primary_key=True)
    tenant = Column(String(128), nullable=False, index=True)
    configuration = Column(JSON, nullable=False)
    token_hash = Column(String(64), nullable=False)


class Observation(Base):
    __tablename__ = "meter_observations"
    __table_args__ = (UniqueConstraint("device", "timestamp"),)
    id = Column(Integer, primary_key=True)
    device = Column(String(32), nullable=False, index=True)
    timestamp = Column(String(40), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(8), nullable=False)
    quality = Column(JSON, nullable=False)


class Reading(Input):
    timestamp: AwareDatetime
    value: float = Field(ge=0, le=1e12, allow_inf_nan=False)
    unit: Literal["L", "mL", "kL", "m3", "Wh", "kWh", "kW", "W"]
    occupied: bool | None = None
    scheduled: bool | None = None
    equipment_on: bool | None = None


@router.post("/devices", status_code=201)
def register_device(body: DeviceInput, member: Member = Depends(require_member)):
    admin(member)
    if (body.tariff_paise_per_unit is None) != (body.tariff_source is None):
        raise HTTPException(422, "Supply both a per-interval-unit tariff and its source.")
    token = secrets.token_urlsafe(32)
    with Session(engine) as db:
        if body.parent_device_id:
            parent = db.get(Device, body.parent_device_id)
            if not parent or parent.tenant != member.tenant or parent.configuration["metric"] != body.metric:
                raise HTTPException(422, "Parent must be a registered compatible facility meter.")
            for field in ("campus_id","building_id","floor_id","room_id"):
                expected = parent.configuration.get(field)
                if expected and getattr(body, field) != expected:
                    raise HTTPException(422, "Child hierarchy conflicts with the registered parent.")
        device = Device(id=secrets.token_hex(16), tenant=member.tenant, configuration=body.model_dump(mode="json"),
                        token_hash=hashlib.sha256(token.encode()).hexdigest())
        db.add(device)
        db.commit()
        return {"id": device.id, "device_token": token}


@router.post("/devices/{identifier}/telemetry")
def ingest(identifier: str, readings: list[Reading], request: Request):
    if not 1 <= len(readings) <= 500:
        raise HTTPException(422, "Expected 1 to 500 observations.")
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    with Session(engine) as db:
        device = db.get(Device, identifier)
        if scheme.lower() != "bearer" or not device or not secrets.compare_digest(
                device.token_hash, hashlib.sha256(token.encode()).hexdigest()):
            raise HTTPException(401, "Device authentication required.")
        return store_readings(db, device, readings, "device_http")


def validate_readings(device, readings, timestamp):
    for reading in readings:
        if (UNIT_CONVERSION[reading.unit][0] != UNITS[device.configuration["metric"]] or
                not timestamp - timedelta(days=30) <= reading.timestamp <= timestamp + timedelta(minutes=2)):
            raise HTTPException(422, "Unit or timestamp outside device limits.")


def store_readings(db, device, readings, source):
    identifier = device.id
    timestamp = now()
    validate_readings(device, readings, timestamp)
    count = 0
    for reading in readings:
        instant = reading.timestamp.astimezone(timestamp.tzinfo).isoformat()
        quality = reading.model_dump(include={"occupied", "scheduled", "equipment_on"})
        unit, scale = UNIT_CONVERSION[reading.unit]
        value = reading.value * scale
        quality.update(validation_status="validated", original_value=reading.value, original_unit=reading.unit, source=source, original_timestamp=reading.timestamp.isoformat(), calibration_ref=device.configuration["calibration_ref"])
        query = select(Observation).where(Observation.device == identifier, Observation.timestamp == instant)
        previous = db.scalar(query)
        if previous is None:
            try:
                with db.begin_nested():
                    db.add(Observation(device=identifier, timestamp=instant, value=value, unit=unit, quality=quality))
                    db.flush()
                count += 1
            except IntegrityError:
                previous = db.scalar(query)
                if previous is None:
                    raise
        if previous is not None and (previous.value != value or any(previous.quality.get(key) != quality[key] for key in ("occupied", "scheduled", "equipment_on"))):
            raise HTTPException(409, "Conflicting reading for an existing timestamp.")
    db.commit()
    return {"inserted": count, "duplicates": len(readings) - count}


@router.post("/devices/{identifier}/import")
async def import_readings(identifier: str, file: UploadFile = File(...), mapping: str = Form("{}"),
                          preview: bool = Form(True), member: Member = Depends(require_member)):
    import json
    from core.data_processor import _parse_bytes
    content = await file.read(2 * 1024 * 1024 + 1)
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(413, "Meter imports are limited to 2 MiB.")
    try:
        frame = _parse_bytes(content, file.filename or "", json.loads(mapping))
        if not 1 <= len(frame) <= 500:
            raise ValueError()
        readings = [Reading(**r) for r in frame.to_dict("records")]
    except (ValueError, TypeError, KeyError, OSError, BadZipFile, ParseError, csv.Error):
        raise HTTPException(422, "Map timestamp, unit and value to at most 500 valid observations.")
    with Session(engine) as db:
        device = db.scalar(select(Device).where(Device.id == identifier, Device.tenant == member.tenant))
        if device is None:
            raise HTTPException(404, "Device unavailable.")
        if preview:
            validate_readings(device, readings, now())
            return {"rows": len(readings), "preview": [r.model_dump() for r in readings[:5]]}
        return store_readings(db, device, readings, "staff_import")


@router.post("/devices/{identifier}/manual")
def manual_reading(identifier: str, reading: Reading, member: Member = Depends(require_member)):
    with Session(engine) as db:
        device = db.scalar(select(Device).where(Device.id == identifier, Device.tenant == member.tenant))
        if device is None:
            raise HTTPException(404, "Device unavailable.")
        return store_readings(db, device, [reading], "manual_meter_reading")


@router.get("/devices/{identifier}/observations")
def observations(identifier: str, member: Member = Depends(require_member)):
    with Session(engine) as db:
        device = db.scalar(select(Device).where(Device.id == identifier, Device.tenant == member.tenant))
        if device is None:
            raise HTTPException(404, "Device unavailable.")
        config = device.configuration
        rows = list(reversed(db.scalars(select(Observation).where(Observation.device == identifier)
                             .order_by(Observation.timestamp.desc()).limit(500)).all()))
        current = now()
        result = []
        recent_rates = []
        intervals = []
        for i, row in enumerate(rows):
            t = datetime.fromisoformat(row.timestamp)
            seconds = None
            quality = "initial"
            delta = None
            if i:
                prev = rows[i-1]
                seconds = (t - datetime.fromisoformat(prev.timestamp)).total_seconds()
                if seconds > config["interval_seconds"] * 2:
                    quality = "gap"
                elif config["metric"] == "power":
                    quality, delta = "integrated", (row.value + prev.value) / 2 * seconds / 3600
                elif row.value < prev.value:
                    quality = "counter_reset"
                else:
                    quality, delta = "difference", row.value - prev.value
            if delta is not None:
                rate = delta / seconds
                evidence = (row.quality.get("occupied"), row.quality.get("scheduled"), row.quality.get("equipment_on"))
                baseline = [r for hour, context, r in recent_rates if hour == t.hour and context == evidence]
                sustained = (evidence[0] is not None and len(baseline) >= 3 and rate > 0 and
                             rate > median(baseline) * (1.5 + config["uncertainty_fraction"]))
                intervals.append((sustained, row.timestamp))
                recent_rates.append((t.hour, evidence, rate))
            else:
                intervals.clear()
            result.append(dict(cost_paise=round(delta * config["tariff_paise_per_unit"]) if delta is not None and config.get("tariff_paise_per_unit") is not None else None, duration_seconds=seconds, context=row.quality, timestamp=row.timestamp, value=row.value, unit=row.unit, quality=quality, interval_total=delta))
        calibrated = datetime.fromisoformat(config["calibration_due"]) >= current
        findings = []
        stale = not rows or (current-datetime.fromisoformat(rows[-1].timestamp)).total_seconds() > 2*config["interval_seconds"]
        if not stale and calibrated and len(intervals) >= 3 and all(flag for flag, _ in intervals[-3:]):
            label = "Persistent elevated water use" if config["metric"] == "water_counter" else "Persistent elevated metered load"
            findings.append(dict(label=label, zone_id=config["zone_id"], timestamps=[t for _, t in intervals[-3:]],
                                 basis="Three consecutive intervals above matched UTC-hour and occupancy/schedule baseline.",
                                 next_step="Authorized facility staff should inspect this instrumented zone."))
        return dict(tariff_source=config.get("tariff_source"), findings=findings, device=identifier, zone_id=config["zone_id"], metric=config["metric"], source=rows[-1].quality.get("source") if rows else None,
                    calibrated=datetime.fromisoformat(config["calibration_due"]) >= current,
                    stale=stale,
                    interval_unit="L" if config["metric"] == "water_counter" else "kWh", readings=result)

class WorkOrder(Base):
    __tablename__ = "meter_work_orders"
    id = Column(String(32), primary_key=True)
    device = Column(String(32), nullable=False)
    tenant = Column(String(128), nullable=False, index=True)
    evidence = Column(JSON, nullable=False)
    result = Column(JSON(none_as_null=True))


@router.post("/devices/{identifier}/work-orders")
def open_work_order(identifier: str, member: Member = Depends(require_member)):
    admin(member)
    data = observations(identifier, member)
    if not data["findings"] or data["stale"]:
        raise HTTPException(409, "Current calibrated meter evidence required.")
    evidence = data["readings"][-3:]
    key = hashlib.sha256((identifier + evidence[-1]["timestamp"]).encode()).hexdigest()[:32]
    with Session(engine) as db:
        row = db.get(WorkOrder, key)
        if row is None:
            row = WorkOrder(id=key, tenant=member.tenant, device=identifier,
                            evidence={"readings": evidence, "zone": data["zone_id"], "opened": now().isoformat()})
            db.add(row)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                row = db.get(WorkOrder, key)
                if row is None:
                    raise
        return {"id": key, "zone": row.evidence["zone"], "status": "reviewed" if row.result else "open"}


class Maintenance(Input):
    maintenance_ref: Name
    completed_at: AwareDatetime


@router.post("/work-orders/{identifier}/verify")
def verify_work_order(identifier: str, body: Maintenance, member: Member = Depends(require_member)):
    from sqlalchemy import update
    admin(member)
    with Session(engine) as db:
        row = db.scalar(select(WorkOrder).where(WorkOrder.id == identifier, WorkOrder.tenant == member.tenant))
        if row is None:
            raise HTTPException(404, "Work order unavailable.")
        if row.result:
            return row.result
        data = observations(row.device, member)
        before = row.evidence["readings"]
        if body.completed_at <= datetime.fromisoformat(row.evidence["opened"]):
            raise HTTPException(422, "Maintenance must follow the work order.")
        after = data["readings"][-3:]
        def context(readings):
            return [(r["timestamp"][11:19], r["duration_seconds"], r["context"]["occupied"], r["context"]["scheduled"], r["context"].get("equipment_on")) for r in readings]
        if (not data["calibrated"] or data["stale"] or len(after) != len(before)
                or context(before) != context(after) or any(r["context"]["occupied"] is None for r in after)
                or any(r["interval_total"] is None or datetime.fromisoformat(r["timestamp"]) - timedelta(seconds=r["duration_seconds"]) < body.completed_at for r in after)):
            raise HTTPException(409, "Comparable calibrated post-maintenance observations required.")
        result = dict(maintenance_ref=body.maintenance_ref, measured_difference=sum(r["interval_total"] for r in before)
                      - sum(r["interval_total"] for r in after), unit=data["interval_unit"], after=after,
                      verified_by=member.subject, verified_at=now().isoformat(), basis="Matched time and occupancy.")
        updated = db.execute(update(WorkOrder).where(WorkOrder.id == identifier, WorkOrder.result.is_(None)).values(result=result))
        if updated.rowcount != 1:
            raise HTTPException(409, "Work order already reviewed.")
        db.commit()
        return result

@router.get("/devices")
def list_devices(member: Member = Depends(require_member)):
    with Session(engine) as db:
        rows = db.scalars(select(Device).where(Device.tenant == member.tenant).order_by(Device.id).limit(500))
        return [{"id": row.id, "zone_id": row.configuration["zone_id"], "metric": row.configuration["metric"]}
                for row in rows]


@router.get("/devices/{identifier}/balance")
def meter_balance(identifier: str, member: Member = Depends(require_member)):
    from math import fsum
    with Session(engine) as db:
        parent = db.scalar(select(Device).where(Device.id == identifier, Device.tenant == member.tenant))
        if not parent:
            raise HTTPException(404, "Device unavailable.")
        children = [r for r in db.scalars(select(Device).where(Device.tenant == member.tenant))
                    if r.configuration.get("parent_device_id") == identifier]
        if not children:
            return {"available": False, "reason": "No registered child meters."}
        series = [observations(d.id, member) for d in [parent, *children]]
        if any(not s["calibrated"] or s["stale"] or not s["readings"] for s in series):
            return {"available": False, "reason": "Current calibrated readings required for every registered meter."}
        rows = [s["readings"][-1] for s in series]
        if any(r["interval_total"] is None or r["timestamp"] != rows[0]["timestamp"] or
               r["duration_seconds"] != rows[0]["duration_seconds"] for r in rows):
            return {"available": False, "reason": "Synchronized interval boundaries required."}
        residual = rows[0]["interval_total"] - fsum(r["interval_total"] for r in rows[1:])
        uncertainty = fsum(r["interval_total"] * d.configuration["uncertainty_fraction"]
                           for r,d in zip(rows,[parent,*children]))
        return dict(available=True, zone_id=parent.configuration["zone_id"], timestamp=rows[0]["timestamp"],
                    residual=residual, uncertainty=uncertainty, unit=series[0]["interval_unit"],
                    interpretation="Unaccounted metered consumption including any uninstrumented branches.")
