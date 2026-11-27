"""Tenant-scoped recovery missions and staff-reviewed service coverage."""
from contextlib import contextmanager
import hashlib
import json
import re
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator
from sqlalchemy import JSON, Column, Integer, LargeBinary, String, UniqueConstraint, func, select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from agents.waste_agent import analyze_waste, normalize_waste_key
from core.ai_client import call_ai, ai_status
from core.execution_queue import InvestigationLease, LostLease, ExecutionJob
from core.auth import Member, require_member
from core.database import Base, engine, get_run_by_id, AccessAudit

router = APIRouter(tags=["Recovery"])
Pin = Annotated[str, StringConstraints(pattern=r"^[1-9][0-9]{5}$")]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
Mass = Annotated[int, Field(strict=True, gt=0, le=100000000)]
Money = Annotated[int, Field(strict=True, ge=0, le=1000000000)]
Pathway = Literal["sell", "donate", "reuse", "repair", "internal_redistribution", "upcycling", "composting", "industrial_symbiosis", "collective_recovery", "recycling", "authorized_disposal"]


def now():
    return datetime.now(timezone.utc)


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Batch(Input):
    request_id: uuid.UUID
    material: Name
    quantity_g: Mass
    service_pin: Pin
    condition: Name
    contaminated: bool
    mixed_inventory: bool = False
    use_context: Name | None = None
    photo_id: uuid.UUID | None = None
    preferred_effort: Literal["low", "moderate", "any"] = "any"
    goal: Pathway = "recycling"
    collective_consent: bool = False
    collection_date: date | None = None
    supply_expires: AwareDatetime | None = None


class Service(Input):
    organization: Name
    registration: Literal["organization", "assisted_collector"] = "organization"
    pathway: Pathway
    material: Name
    condition: Name
    service_pins: list[Pin] = Field(min_length=1, max_length=100)
    minimum_g: Mass
    capacity_g: Mass
    expires: AwareDatetime
    identity_evidence: Name
    publication_consent: bool = False
    business_email: Annotated[str, StringConstraints(max_length=160, pattern=r"^(info|office|recovery|service|operations|contact)@[a-z0-9-]+(\.[a-z0-9-]+)+$")] | None = None
    acceptance_evidence: Name
    consent_evidence: Name
    regulatory_evidence: Name | None = None
    quote_paise_per_kg: Money | None = None
    quote_expires: AwareDatetime | None = None
    avoided_purchase_paise: Money | None = None
    avoided_co2e_g_per_kg: int | None = Field(default=None, ge=0, le=1000000)
    environmental_evidence: Name | None = None
    preparation: Name | None = None
    effort: Literal["low", "moderate", "high"] = "moderate"
    collection_paise: Money | None = None
    collection_start: date | None = None
    collection_end: date | None = None
    fees_paise: Money = 0
    transport_paise: Money = 0
    preparation_paise: Money = 0
    transfer: Literal["pickup", "dropoff", "internal"]

    @model_validator(mode="after")
    def check_limits(self):
        if (self.avoided_co2e_g_per_kg is None) != (self.environmental_evidence is None):
            raise ValueError("Provide the reviewed comparison evidence for the projected environmental benefit.")
        if self.pathway == "authorized_disposal" and not self.regulatory_evidence:
            raise ValueError("Authorized disposal requires a regulatory evidence reference.")
        if self.collection_start and self.collection_end and self.collection_start > self.collection_end:
            raise ValueError("Collection end precedes the start.")
        if self.minimum_g > self.capacity_g or self.expires <= now():
            raise ValueError("Current capacity and expiry are required.")
        return self


class Mission(Base):
    __tablename__ = "recovery_missions"
    __table_args__ = (UniqueConstraint("tenant", "request_id"),)
    id = Column(String(36), primary_key=True)
    tenant = Column(String(128), nullable=False, index=True)
    request_id = Column(String(36), nullable=False)
    inputs = Column(JSON, nullable=False)
    state = Column(String(40), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    events = Column(JSON, nullable=False)
    result = Column(JSON, nullable=False)
    service_id = Column(String(36))
    passport = Column(String(64), unique=True)


class Directory(Base):
    __tablename__ = "recovery_services"
    id = Column(String(36), primary_key=True)
    tenant = Column(String(128), nullable=False, index=True)
    details = Column(JSON, nullable=False)
    status = Column(String(12), nullable=False)
    remaining_g = Column(Integer, nullable=False)
    audit = Column(JSON, nullable=False)


class MaterialPhoto(Base):
    __tablename__ = "material_photos"
    id = Column(String(36), primary_key=True)
    tenant = Column(String(128), nullable=False, index=True)
    jpeg = Column(LargeBinary, nullable=False)
    created_at = Column(String(40), nullable=False)


class MaterialGuidance(Base):
    __tablename__ = "material_guidance"
    __table_args__ = (UniqueConstraint("tenant", "material"),)
    id = Column(String(36), primary_key=True)
    tenant = Column(String(128), nullable=False, index=True)
    material = Column(String(160), nullable=False)
    details = Column(JSON, nullable=False)


class ServiceOutcome(Base):
    __tablename__ = "service_outcomes"
    id = Column(Integer, primary_key=True)
    mission_id = Column(String(36), nullable=False)
    service_id = Column(String(36), nullable=False, index=True)
    offered_g = Column(Integer, nullable=False)
    accepted_g = Column(Integer, nullable=False)
    rejected = Column(Integer, nullable=False)


def event(agent, action, **details):
    return dict(at=now().isoformat(), agent=agent, action=action, **details)


def admin(member):
    if member.role != "admin":
        raise HTTPException(403, "Authorized facility administrator required.")


def owned(db, table, identifier, member):
    row = db.scalar(select(table).where(table.id == identifier, table.tenant == member.tenant))
    if row is None:
        raise HTTPException(404, "Record unavailable.")
    return row


@router.post("/recovery/photos", status_code=201)
async def material_photo(file: UploadFile = File(...), member: Member = Depends(require_member)):
    from io import BytesIO
    from PIL import Image, ImageOps
    raw = await file.read(2*1024*1024+1)
    if len(raw) > 2*1024*1024:
        raise HTTPException(413, "Photo exceeds 2 MiB.")
    try:
        with Image.open(BytesIO(raw), formats=("JPEG", "PNG")) as image:
            if image.width * image.height > 4000000:
                raise ValueError()
            pixels = ImageOps.exif_transpose(image).convert("RGB")
            pixels.thumbnail((1200,1200))
            buffer = BytesIO()
            pixels.save(buffer, format="JPEG", quality=80)
    except (ValueError, OSError, Image.DecompressionBombError):
        raise HTTPException(422, "Expected a valid material photo under four megapixels.")
    with Session(engine) as db:
        row = MaterialPhoto(id=str(uuid.uuid4()), tenant=member.tenant, jpeg=buffer.getvalue(), created_at=now().isoformat())
        db.add(row)
        db.commit()
        return {"id":row.id}


@router.get("/recovery/photos/{identifier}")
def inspect_photo(identifier: str, member: Member = Depends(require_member)):
    from fastapi.responses import Response
    with Session(engine) as db:
        row = owned(db, MaterialPhoto, identifier, member)
        jpeg = row.jpeg
        db.add(AccessAudit(tenant=member.tenant, subject=member.subject, action="view_material_photo"))
        db.commit()
        return Response(jpeg, media_type="image/jpeg", headers={"Cache-Control":"no-store"})


class Guidance(Input):
    material: Name
    source_document: Name
    review_question: Name
    expires: AwareDatetime


@router.post("/recovery/guidance")
def approve_guidance(body: Guidance, member: Member = Depends(require_member)):
    admin(member)
    if body.expires <= now():
        raise HTTPException(422, "Current source review required.")
    with Session(engine) as db:
        key = normalize_waste_key(body.material)
        row = db.scalar(select(MaterialGuidance).where(MaterialGuidance.tenant == member.tenant, MaterialGuidance.material == key))
        if row is None:
            row = MaterialGuidance(id=str(uuid.uuid4()), tenant=member.tenant, material=key)
            db.add(row)
        row.details = {**body.model_dump(mode="json"), "reviewer":member.subject, "reviewed_at":now().isoformat()}
        db.commit()
        return {"id":row.id}


@router.post("/recovery/services", status_code=201)
def submit_service(body: Service, member: Member = Depends(require_member)):
    details = body.model_dump(mode="json")
    details["material"] = normalize_waste_key(body.material)
    with Session(engine) as db:
        row = Directory(id=str(uuid.uuid4()), tenant=member.tenant, details=details,
                        remaining_g=body.capacity_g, status="pending",
                        audit=[event("Directory", "submitted", by=member.subject)])
        db.add(row)
        db.commit()
        return {"id": row.id, "status": row.status}


class Review(Input):
    decision: Literal["verified", "revoked", "suspended"]
    confirmation_ref: Name
    publication_ref: Name | None = None
    verification_expires: AwareDatetime | None = None


@router.post("/recovery/services/{identifier}/review")
def review_service(identifier: str, body: Review, member: Member = Depends(require_member)):
    admin(member)
    with Session(engine) as db:
        row = owned(db, Directory, identifier, member)
        if body.decision == "verified" and (row.audit[0]["by"] == member.subject or
                datetime.fromisoformat(row.details["expires"]) <= now()):
            raise HTTPException(409, "Independent current review required.")
        if body.verification_expires and body.verification_expires <= now():
            raise HTTPException(422, "Verification must have a future expiry.")
        details = dict(row.details)
        details["verification_expires"] = body.verification_expires.isoformat() if body.verification_expires else details["expires"]
        details["publication_ref"] = body.publication_ref if body.decision == "verified" else None
        row.details = details
        row.status = body.decision
        row.audit = [*row.audit, event("Directory", body.decision, by=member.subject, evidence=body.confirmation_ref)]
        db.commit()
        return {"status": row.status}


@router.get("/recovery/services")
def manage_services(member: Member = Depends(require_member)):
    admin(member)

    with Session(engine) as db:
        rows = db.scalars(
            select(Directory)
            .where(Directory.tenant == member.tenant)
            .order_by(Directory.id)
            .limit(200)
        ).all()

        return [
            {
                "id": row.id,
                "organization": row.details["organization"],
                "pathway": row.details["pathway"],
                "material": row.details["material"],
                "condition": row.details["condition"],
                "service_pins": row.details["service_pins"],
                "remaining_g": row.remaining_g,
                "capacity_g": row.details["capacity_g"],
                "expires": row.details["expires"],
                "verification_expires": row.details.get(
                    "verification_expires"
                ),
                "status": row.status,
                "fees_paise": row.details.get("fees_paise"),
                "transport_paise": row.details.get("transport_paise"),
                "preparation_paise": row.details.get("preparation_paise"),
                "avoided_purchase_paise": row.details.get("avoided_purchase_paise"),
                "avoided_co2e_g_per_kg": row.details.get("avoided_co2e_g_per_kg"),
                "environmental_evidence": row.details.get("environmental_evidence"),
                "preparation": row.details.get("preparation"),
                "effort": row.details.get("effort"),
                "transfer": row.details.get("transfer"),
                "publication_requested": bool(row.details.get("publication_consent") and row.details.get("business_email")),
                "identity_evidence": row.details["identity_evidence"],
                "acceptance_evidence": row.details["acceptance_evidence"],
                "consent_evidence": row.details["consent_evidence"],
                "regulatory_evidence": row.details.get("regulatory_evidence"),
                "quote_paise_per_kg": row.details.get("quote_paise_per_kg"),
                "quote_expires": row.details.get("quote_expires"),
                "audit": [
                    {
                        "at": entry.get("at"),
                        "action": entry.get("action"),
                        "evidence": entry.get("evidence"),
                    }
                    for entry in row.audit
                ],
            }
            for row in rows
        ]


@router.get("/recovery/opportunities")
def recovery_opportunities(member: Member = Depends(require_member)):
    with Session(engine) as db:
        rows = db.scalars(select(Directory).where(Directory.tenant == member.tenant,
                          Directory.status == "verified", Directory.remaining_g > 0).order_by(Directory.id))
        result = []
        for row in rows:
            details = row.details
            if not all(details.get(key) and datetime.fromisoformat(details[key]) > now()
                       for key in ("verification_expires", "expires")):
                continue
            quote_until = details.get("quote_expires") or details["expires"]
            result.append({**{key: details[key] for key in ("organization", "material", "condition",
                "service_pins", "transfer", "pathway", "expires", "verification_expires")},
                "status": row.status, "remaining_g": row.remaining_g, "id": row.id,
                "collection_start": details.get("collection_start"), "collection_end": details.get("collection_end"),
                "minimum_g": details["minimum_g"], "quote_expires": quote_until, "quote_paise_per_kg": details.get("quote_paise_per_kg")
                if datetime.fromisoformat(quote_until) > now() else None})
        return result


@router.get("/recovery/directory/{pin}")
def published_services(pin: Pin, member: Member = Depends(require_member)):
    with Session(engine) as db:
        rows = db.scalars(select(Directory).where(Directory.tenant == member.tenant, Directory.status == "verified"))
        result = []
        for row in rows:
            d = row.details
            if pin not in d["service_pins"] or min(datetime.fromisoformat(d[k]) for k in
                    ("expires", "verification_expires") if d.get(k)) <= now():
                continue
            if d.get("publication_consent") and d.get("publication_ref") and d.get("business_email"):
                result.append({"id": row.id, "organization": d["organization"], "service_pin":pin,
                               "material":d["material"], "business_email":d["business_email"]})
        return result


@router.delete("/recovery/services/{identifier}/publication")
def withdraw_publication(identifier: str, member: Member = Depends(require_member)):
    with Session(engine) as db:
        row = owned(db, Directory, identifier, member)
        if row.audit[0]["by"] != member.subject:
            admin(member)
        row.details = {**row.details, "publication_consent":False, "publication_ref":None}
        row.audit = [*row.audit, event("Directory", "publication_withdrawn", by=member.subject)]
        db.commit()
        return {"published":False}


class Interpretation(Input):
    evidence: list[Name] = Field(min_length=1, max_length=8)
    proposed_material: Name | None = None
    issue: Literal["composition", "separation", "supplier_label", "condition"]


def material_question(batch, reason):
    description = batch.material + (" " + batch.use_context if batch.use_context else "")
    questions = {
        "composition": "Which constituents does the supplier label identify?",
        "separation": "Are these separate weighed lots or one bonded composite?",
        "supplier_label": "What material and specification appear on the supplier label?",
        "condition": "What condition or contamination did authorized facility staff document?",
    }
    issue = "separation" if re.search(r"bonded|composite|mixed|laminated|layer|\band\b", description, re.I) else "supplier_label"
    evidence = [batch.material]
    provider = proposed = None
    if batch.contaminated:
        issue = "condition"
    else:
        prompt = ("Identify the missing evidence for an adult facility reviewer. Return JSON with only "
                  "issue (composition, separation, supplier_label or condition) and evidence "
                  "(verbatim fragments of the description), and optional proposed_material (a verbatim candidate from the label). Input: " + json.dumps(description))
        # Material descriptions may contain private identifiers. Keep free text local.
        from core.ai_client import _cloud_consent
        consent = _cloud_consent.set(False)
        try:
            raw, used = call_ai(prompt, "", schema=Interpretation)
        finally:
            _cloud_consent.reset(consent)
        if used:
            proposal = Interpretation.model_validate_json(raw)
            if all(fragment in description for fragment in proposal.evidence) and (
                    proposal.proposed_material is None or proposal.proposed_material in description):
                proposed = proposal.proposed_material
                issue, evidence = proposal.issue, proposal.evidence
                provider = ai_status()["provider"]
    question = reason if "Source:" in reason else questions[issue]
    return dict(question=question, issue=issue, evidence=evidence, provider=provider, proposed_material=proposed,
                status="requires_facility_evidence")


class ClassifiedLot(Input):
    material: Name
    condition: Name
    quantity_g: Mass
    contaminated: bool


class Clarification(Input):
    version: int = Field(ge=1)
    answer: Name
    evidence_ref: Name
    disposition: Literal["unresolved", "identified", "separate_lots"]
    lots: list[ClassifiedLot] = Field(default_factory=list, max_length=30)


@router.post("/missions/{identifier}/clarifications")
def clarify_material(identifier: str, body: Clarification, member: Member = Depends(require_member)):
    with mission_inference(member, identifier=identifier):
        return _apply_clarify_material(identifier, body, member)


def _apply_clarify_material(identifier: str, body: Clarification, member: Member):
    admin(member)
    with Session(engine) as db:
        row = owned(db, Mission, identifier, member)
        digest = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
        if row.events[-1].get("request_hash") == digest and row.events[-1].get("by") == member.subject:
            return current_snapshot(db, row)
        if row.state != "manual_review" or row.version != body.version:
            raise HTTPException(409, "Refresh the open material review.")
        batch = Batch(**row.inputs)
        lots = body.lots
        if (body.disposition == "unresolved" and lots or
                body.disposition == "identified" and len(lots) != 1 or
                body.disposition == "separate_lots" and len(lots) < 2 or
                lots and sum(lot.quantity_g for lot in lots) != batch.quantity_g):
            raise HTTPException(422, "Account for the whole batch in distinct weighed lots.")
        original = analyze_waste(batch.material, batch.quantity_g / 1000, narrative=False)
        professional = bool(original.get("hazard_warning") or batch.contaminated)
        review = dict(answer=body.answer, evidence_ref=body.evidence_ref, reviewer=member.subject,
                      disposition=body.disposition, question=row.result.get("clarification"))
        result = {**row.result, "original_inputs":row.inputs, "review":review, "options":[]}
        events = [*row.events]
        state, inputs = "professional_review", row.inputs
        if lots:
            result["classification"] = review
            result["lots"] = []
        children = []
        for i, lot in enumerate(lots):
            item = batch.model_copy(update={**lot.model_dump(), "mixed_inventory":False, "contaminated":professional or lot.contaminated})
            trace = []
            next_state, matches, reason = options(db, member.tenant, item, reviewed=True, trace=trace)
            trace.append(event("Waste-to-Wealth Agent", next_state, reason=reason))
            if len(lots) == 1:
                inputs, state = item.model_dump(mode="json"), next_state
                result["options"] = matches
                events.extend(trace)
            else:
                child_id = str(uuid.uuid5(uuid.UUID(row.id), str(i)))
                item.request_id = uuid.UUID(child_id)
                children.append(Mission(id=child_id, tenant=row.tenant, request_id=child_id, inputs=item.model_dump(mode="json"),
                               state=next_state, events=trace, result={"options":matches, "classification":review,
                               "inventory_id":row.id}))
                result["lots"].append({"id":child_id, **lot.model_dump()})
                state = "inventory_split"
        events.append(event("Waste-to-Wealth Agent", "clarification_recorded", state=state, by=member.subject,
                            evidence=body.evidence_ref, request_hash=digest))
        changed = db.execute(update(Mission).where(Mission.id == row.id, Mission.version == body.version)
                             .values(inputs=inputs, result=result, state=state, events=events, version=body.version+1))
        if changed.rowcount != 1:
            raise HTTPException(409, "Concurrent material review.")
        db.add_all(children)
        db.commit()
        return current_snapshot(db, row)


def compatible_lots(first, other):
    return (first.collective_consent and other.collective_consent and not other.contaminated
            and not first.contaminated and first.collection_date == other.collection_date
            and first.service_pin == other.service_pin and first.condition.casefold() == other.condition.casefold()
            and normalize_waste_key(first.material) == normalize_waste_key(other.material))


def collective_candidates(db, tenant, batch):
    rows = db.scalars(select(Mission).where(Mission.tenant == tenant, Mission.request_id != str(batch.request_id),
                      Mission.state.in_(["awaiting_approval","needs_evidence"])).order_by(Mission.id).limit(100))
    candidates = []
    for row in rows:
        if row.inputs.get("kind") == "analysis" or row.result.get("sources"):
            continue
        other = Batch(**row.inputs)
        if compatible_lots(batch, other) and batch.quantity_g + other.quantity_g <= 100000000:
            combined = batch.model_copy(update={"quantity_g":batch.quantity_g + other.quantity_g})
            _, matches, _ = options(db, tenant, combined, collective_only=True)
            if matches:
                candidates.append({"mission_id":row.id, "combined_g":combined.quantity_g,
                                   "service_id":matches[0]["service_id"]})
                if len(candidates) == 5:
                    break
    return candidates


def recorded_recovery_attempts(events):
    total = 0

    for entry in events:
        intelligence = entry.get("intelligence") or {}
        attempts = intelligence.get("inference_attempts", entry.get("inference_attempts", 0))

        if type(attempts) is int and attempts >= 0:
            total += attempts

    return total


@contextmanager
def mission_inference(member, *, identifier=None, request_id=None):
    from core.ai_client import inference_enabled, _mission_allowance
    from core.database import MissionInferenceBudget as Budget
    if not inference_enabled():
        yield
        return
    from sqlalchemy.dialects import postgresql, sqlite
    with Session(engine) as db:
        row = owned(db, Mission, identifier, member) if identifier else db.scalar(select(Mission).where(
            Mission.tenant == member.tenant, Mission.request_id == str(request_id)))
        key = str(row.request_id if row else request_id)
        historical = min(3, max(recorded_recovery_attempts(row.events), row.result.get("inference_attempts", 0))) if row else 0
        insert = postgresql.insert if engine.dialect.name == "postgresql" else sqlite.insert
        db.execute(insert(Budget).values(tenant=member.tenant, request_id=key, charged=historical)
                   .on_conflict_do_nothing())
        budget = db.get(Budget, (member.tenant, key), with_for_update=True)
        remaining = 3 - max(historical, budget.charged)
        budget.charged = 3
        db.commit()
    allowance = {"limit": remaining, "attempts": 0}
    token = _mission_allowance.set(allowance)
    try:
        yield
    finally:
        _mission_allowance.reset(token)
        unused = remaining - allowance["attempts"]
        if unused:
            # A process crash leaves reserved slots charged, preventing an overrun.
            with Session(engine) as db:
                db.execute(update(Budget).where(Budget.tenant == member.tenant, Budget.request_id == key)
                           .values(charged=Budget.charged - unused))
                db.commit()


def options(db, tenant, batch, excluded=(), *, reviewed=False, collective_only=False, trace=None):
    if batch.supply_expires and batch.supply_expires <= now():
        return "no_feasible_action", [], "Recorded supply availability has expired."
    material = analyze_waste(batch.material, batch.quantity_g / 1000, narrative=False)
    professional = bool(batch.contaminated or material.get("hazard_warning"))
    if trace is not None:
        trace.append(event("Waste-to-Wealth Agent", "material_lookup", material=batch.material,
                           catalogue_status=material["status"], professional_review=professional))
    if (material["status"] != "analyzed" or professional or batch.mixed_inventory) and not reviewed:
        guidance = db.scalar(select(MaterialGuidance).where(MaterialGuidance.tenant == tenant,
                             MaterialGuidance.material == normalize_waste_key(batch.material)))
        if guidance and datetime.fromisoformat(guidance.details["expires"]) > now():
            return "manual_review", [], f"{guidance.details['review_question']} Source: {guidance.details['source_document']}"
        return "manual_review", [], material.get("clarification", "Authorized staff must verify contamination and safe handling.")
    matches = []
    rows = db.scalars(select(Directory).where(Directory.tenant == tenant, Directory.status == "verified"))
    history = dict((service_id, (count, rejections, accepted, offered)) for service_id, count, rejections, accepted, offered in
        db.execute(select(ServiceOutcome.service_id, func.count(ServiceOutcome.id), func.sum(ServiceOutcome.rejected),
                          func.sum(ServiceOutcome.accepted_g), func.sum(ServiceOutcome.offered_g)).join(
            Directory, Directory.id == ServiceOutcome.service_id).where(Directory.tenant == tenant).group_by(ServiceOutcome.service_id)))
    current = now()
    service_zone = timezone(timedelta(hours=5, minutes=30))

    def expired(value):
        until = datetime.fromisoformat(value)
        return until <= current or (batch.collection_date is not None and
                                    until.astimezone(service_zone).date() < batch.collection_date)

    for row in rows:
        d = row.details
        if ((professional and d["pathway"] != "authorized_disposal")
                or (collective_only and d["pathway"] != "collective_recovery")
                or row.id in excluded or d["material"] != normalize_waste_key(batch.material)
                or d["condition"].casefold() != batch.condition.casefold() or batch.service_pin not in d["service_pins"]
                or not d["minimum_g"] <= batch.quantity_g <= row.remaining_g
                or expired(d.get("verification_expires") or d["expires"]) or expired(d["expires"])
                or (d["pathway"] == "collective_recovery" and not batch.collective_consent)):
            continue
        if d.get("collection_start") or d.get("collection_end"):
            if not batch.collection_date:
                continue
            day = batch.collection_date.isoformat()
            if d.get("collection_start") and day < d["collection_start"] or d.get("collection_end") and day > d["collection_end"]:
                continue
        rate = d["quote_paise_per_kg"]
        quote_until = d.get("quote_expires") or d["expires"]
        if rate is not None and expired(quote_until):
            if d["pathway"] == "sell":
                continue
            rate = None
        costs = {field: d[field] for field in ("fees_paise", "transport_paise", "preparation_paise")}
        if d.get("collection_paise") is not None:
            costs["collection_paise"] = d["collection_paise"]
        gross = None if rate is None else (rate * batch.quantity_g + 500) // 1000
        net = None if gross is None else gross - sum(costs.values())
        effort_rank = {"low": 0, "moderate": 1, "high": 2, "any": 2}
        if effort_rank[d["effort"]] > effort_rank[batch.preferred_effort]:
            continue
        if d["pathway"] == "sell" and rate is None:
            continue
        benefit = net
        if benefit is None and d.get("avoided_purchase_paise") is not None:
            benefit = d["avoided_purchase_paise"] - sum(costs.values())
        value_score = 0 if benefit is None else min(1, max(0, benefit / 100000))
        # Up to INR 1,000 contributes to value; safety and current acceptance are mandatory filters.
        count, rejections, accepted, offered = history.get(row.id, (0, 0, 0, 0))
        acceptance = accepted / offered if offered else None
        # Only weight measured reliability when handover evidence exists.
        points = 40 * (batch.goal == d["pathway"]) + 30 * value_score + 20 * (1-effort_rank[d["effort"]]/2)
        score = round(points + 10 * acceptance if acceptance is not None else points / 0.9, 2)
        impact = d.get("avoided_co2e_g_per_kg")
        if impact is not None:
            score = round(0.9 * score + 10 * min(1, impact / 1000), 2)
        matches.append(dict(projected_co2e_g=None if impact is None else impact * batch.quantity_g / 1000,
                            environmental_evidence=d.get("environmental_evidence"), score=score, acceptance_fraction=acceptance, outcome_count=count,
                            rejection_fraction=rejections/count if count else None, quote_expires=quote_until if rate is not None else None, effort=d["effort"], avoided_purchase_paise=d["avoided_purchase_paise"], service_id=row.id, organization=d["organization"], pathway=d["pathway"],
                            gross_paise=gross, net_paise=net, quote_paise_per_kg=rate, costs_paise=costs, minimum_g=d["minimum_g"],
                            available_g=row.remaining_g, source=d["acceptance_evidence"], preparation=d.get("preparation"),
                            rationale=f"Reviewed {d['pathway']} service accepts {d['condition']} {d['material']} in this PIN.",
                            next_action=f"Confirm {d['transfer']} capacity with facility staff before approval.",
                            assumption="Quoted return assumes acceptance of the full offered mass.",
                            expires=d["expires"], reviewed_at=next(e["at"] for e in reversed(row.audit) if e["action"] == "verified"), transfer=d["transfer"]))
    matches.sort(key=lambda m: (-m["score"], m["net_paise"] is None, -(m["net_paise"] or 0), m["service_id"]))
    if trace is not None:
        trace.append(event("Waste-to-Wealth Agent", "directory_search", service_pin=batch.service_pin,
                           eligible=len(matches), pathways=sorted({m["pathway"] for m in matches})))
        if matches:
            trace.append(event("Decision Engine Agent", "rank_options", goal=batch.goal,
                               service_ids=[m["service_id"] for m in matches]))
    if matches:
        if trace is not None:
            from core.recovery_intelligence import (
                recovery_intelligence,
            )

            from core.ai_client import _usage

            existing = db.scalar(
                select(Mission).where(
                    Mission.tenant == tenant,
                    Mission.request_id == str(batch.request_id),
                )
            )

            spent = recorded_recovery_attempts(
                existing.events if existing else []
            )

            previous = _usage.get()
            baseline = max(previous, spent)
            token = _usage.set(baseline)

            try:
                intelligence = recovery_intelligence(
                    matches,
                    batch.goal,
                    allow_ai=not professional and baseline < 3,
                )

                consumed = max(0, _usage.get() - baseline)

            finally:
                _usage.reset(token)

            _usage.set(min(3, previous + consumed))

            intelligence["mission_budget"] = {
                "limit": 3,
                "recorded_attempts": spent + consumed,
                "remaining": max(0, 3 - spent - consumed),
            }

            trace.append(event(
                "Decision Engine Agent",
                "evaluate_recovery_alternatives",
                intelligence=intelligence,
            ))

            selected_id = intelligence["selected_service_id"]

            matches.sort(
                key=lambda option: (
                    option["service_id"] != selected_id,
                    -option["score"],
                    option["service_id"],
                )
            )

        return "awaiting_approval", matches, "Eligible services ranked by preferred pathway (40%), net or avoided cost (30%), effort (20%) and observed acceptance (10% when available). Reviewed avoided emissions, when supplied, weight 10% capped at 1 kg CO2e per kg."
    if (trace is not None and not collective_only and batch.collective_consent and batch.collection_date
            and batch.collection_date >= current.astimezone(service_zone).date()):
        candidates = collective_candidates(db, tenant, batch)
        trace.append(event("Waste-to-Wealth Agent", "find_collective", candidates=candidates,
                           reason=f"Found {len(candidates)} eligible pairings for administrator review."))
    return "needs_evidence", [], "No verified match. Staff can register demand or request partner review."


def snapshot(row):
    return dict(id=row.id, state=row.state, version=row.version, inputs=row.inputs, events=row.events,
                recorded_inference_attempts=max(recorded_recovery_attempts(row.events), row.result.get("inference_attempts", 0)),
                result=row.result, passport=row.passport)


def current_snapshot(db, row):
    response = snapshot(row)
    if row.state == "awaiting_approval" and row.inputs.get("kind") != "analysis":
        _, current, _ = options(db, row.tenant, Batch(**row.inputs), row.result.get("excluded", []),
                                reviewed=bool(row.result.get("classification")), collective_only=bool(row.result.get("sources")))
        planned = {
            m["service_id"]: i
            for i, m in enumerate(row.result["options"])
        }
        eligible = [
            m for m in current
            if m["service_id"] in planned
        ]
        eligible.sort(
            key=lambda m: planned[m["service_id"]]
        )
        response["result"] = {
            **row.result,
            "options": eligible,
        }
    return response


@router.post("/missions")
def create_mission(body: Batch, member: Member = Depends(require_member)):
    with mission_inference(member, request_id=body.request_id):
        return _apply_create_mission(body, member)


def _apply_create_mission(body: Batch, member: Member):
    values = body.model_dump(mode="json")
    with Session(engine) as db:
        prior = select(Mission).where(Mission.tenant == member.tenant, Mission.request_id == str(body.request_id))
        row = db.scalar(prior)
        if row is None:
            if body.photo_id:
                owned(db, MaterialPhoto, str(body.photo_id), member)
            trace = []
            state, matches, reason = options(db, member.tenant, body, trace=trace)
            result = {"options": matches}
            if state == "manual_review":
                before = ai_status()["attempts"]
                result["clarification"] = material_question(body, reason)
                result["clarification"]["inference_attempts"] = ai_status()["attempts"] - before
                trace.append(event("Waste-to-Wealth Agent", "request_clarification", **result["clarification"]))
            row = Mission(id=str(uuid.uuid4()), request_id=str(body.request_id), tenant=member.tenant, inputs=values,
                          state=state, result=result, events=[
                              event("Decision Engine Agent", "planned", goal=body.goal),
                              event("Water Leakage Agent", "skipped", reason="No water observations supplied."),
                              event("Energy Optimization Agent", "skipped", reason="No energy observations supplied."),
                              *trace, event("Waste-to-Wealth Agent", state, reason=reason)])
            db.add(row)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                row = db.scalar(prior)
                if row is None:
                    raise
        if row.inputs.get("kind"):
            raise HTTPException(409, "Request identifier belongs to a different mission.")
        original = Batch.model_validate(row.result.get("original_inputs", row.inputs)).model_dump(mode="json")
        if original != values:
            raise HTTPException(409, "Request identifier already used for different inputs.")
        return current_snapshot(db, row)


@router.get("/missions")
def open_material_missions(member: Member = Depends(require_member)):
    with Session(engine) as db:
        rows = db.scalars(select(Mission).where(Mission.tenant == member.tenant,
                          Mission.state.in_(["needs_evidence","awaiting_approval","manual_review","approved"])).limit(200))
        return [{"id": row.id, "state": row.state, "material": row.inputs["material"],
                 "canonical_material": normalize_waste_key(row.inputs["material"]),
                 **{key: row.inputs.get(key) for key in ("condition", "service_pin", "collection_date",
                     "contaminated", "quantity_g", "collective_consent")}}
                for row in rows if row.inputs.get("kind") != "analysis" and not row.result.get("sources")]


@router.get("/missions/{identifier}")
def mission(identifier: str, member: Member = Depends(require_member)):
    with Session(engine) as db:
        row = owned(db, Mission, identifier, member)
        return current_snapshot(db, row)


async def upload_events(upload_mission_id: uuid.UUID | None = Form(None), member: Member = Depends(require_member)):
    """Publish milestones only after the corresponding upload agent returns."""
    from starlette.concurrency import run_in_threadpool
    if upload_mission_id is None:
        async def untracked(*args, **kwargs):
            return
        yield untracked
        return
    identifier = str(upload_mission_id)
    with Session(engine) as db:
        db.add(Mission(id=identifier, tenant=member.tenant, request_id=identifier, inputs={"kind":"upload"},
                       result={"options":[]}, state="processing",
                       events=[event("Decision Engine Agent","upload_received")]))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Upload identifier already used.")

    def persist(agent, action, state="processing", **details):
        with Session(engine) as db:
            row = owned(db, Mission, identifier, member)
            row.events = [*row.events,event(agent,action,**details)]
            row.state = state
            row.version += 1
            if "analysis_id" in details:
                row.result = {**row.result,"analysis_id":details["analysis_id"]}
            db.commit()

    async def record(*args, **kwargs):
        await run_in_threadpool(persist, *args, **kwargs)

    try:
        yield record
    except Exception:
        await record("Decision Engine Agent","upload_failed",state="failed")
        raise


class AnalysisGoal(Input):
    analysis_id: int = Field(gt=0)
    device_id: Annotated[str, StringConstraints(min_length=32,max_length=32)] | None = None
    request_id: uuid.UUID
    goal: Literal["water", "energy", "resource_review"]


_ANALYSIS_TOOLS = {"water": ("Water Leakage Agent", "total_wasted_liters", "L"),
                   "energy": ("Energy Optimization Agent", "total_wasted_kwh", "kWh")}


@router.post("/analysis-missions")
def analysis_mission(body: AnalysisGoal, member: Member = Depends(require_member)):
    run = get_run_by_id(body.analysis_id, tenant=member.tenant)
    if run is None:
        raise HTTPException(404, "Analysis unavailable.")
    inputs = {"kind": "analysis", **body.model_dump(mode="json")}
    with Session(engine) as db:
        query = select(Mission).where(Mission.tenant == member.tenant, Mission.request_id == str(body.request_id))
        row = db.scalar(query)
        if row is None:
            plan = [key for key in _ANALYSIS_TOOLS if body.goal in (key, "resource_review")]
            payload = run.get("payload", {})
            plan.sort(key=lambda key: not bool((payload.get(key) or {}).get("anomaly_detection_available")))
            if body.device_id:
                from core.telemetry import Device
                device = owned(db, Device, body.device_id, member)
                domain = "water" if device.configuration["metric"] == "water_counter" else "energy"
                if domain not in plan:
                    raise HTTPException(422, "Registered meter does not measure the requested domain.")
                plan.insert(0, "meter")
            row = Mission(id=str(uuid.uuid4()), tenant=member.tenant, inputs=inputs, request_id=str(body.request_id),
                          state="planned", result={"pending": plan, "findings": [], "attempts": {}, "options": []},
                          events=[event("Decision Engine Agent", "planned", tools=plan, analysis_id=body.analysis_id),
                                  *[event(meta[0], "skipped", reason="Outside requested goal.")
                                    for key, meta in _ANALYSIS_TOOLS.items() if key not in plan]])
            db.add(row)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                row = db.scalar(query)
                if row is None:
                    raise
        if {"device_id":None, **row.inputs} != inputs:
            raise HTTPException(409, "Request identifier already used for different inputs.")
        return snapshot(row)


class AnalysisStep(Input):
    version: int = Field(ge=1)
    action: Literal["advance", "approve", "verify", "cancel"]
    evidence_ref: Name | None = None
    work_order_id: Name | None = None


class AnalysisExecution(Input):
    version: int = Field(ge=1)
    max_steps: int = Field(default=6, ge=1, le=6)


@router.post("/analysis-missions/{identifier}/execute")
def execute_analysis(
    identifier: str,
    body: AnalysisExecution,
    member: Member = Depends(require_member),
):
    with Session(engine) as db:
        row = owned(db, Mission, identifier, member)

        if row.inputs.get("kind") != "analysis":
            raise HTTPException(404, "Analysis mission unavailable.")

        if row.version != body.version:
            raise HTTPException(409, "Refresh the mission checkpoint.")

        current = snapshot(row)

    completed = 0

    for _ in range(body.max_steps):
        if current["state"] not in ("planned", "in_progress"):
            break

        previous = current["version"]

        current = advance_analysis(
            identifier,
            AnalysisStep(version=previous, action="advance"),
            member,
        )

        if current["version"] <= previous:
            break

        completed += 1

    return {
        "mission": current,
        "completed_steps": completed,
        "stop_reason": (
            "step_limit"
            if current["state"] in ("planned", "in_progress")
            else current["state"]
        ),
    }


@router.post("/analysis-missions/{identifier}/steps")
def advance_analysis(identifier: str, body: AnalysisStep, member: Member = Depends(require_member)):
    return _analysis_step(identifier, body, member)


def _analysis_step(identifier: str, body: AnalysisStep, member: Member | InvestigationLease):
    with mission_inference(member, identifier=identifier):
        return _apply_analysis_step(identifier, body, member)


def _apply_analysis_step(identifier: str, body: AnalysisStep, member: Member | InvestigationLease):
    lease = isinstance(member, InvestigationLease)
    if lease and (body.action != "advance" or member.mission_id != identifier):
        raise LostLease()
    with Session(engine) as db:
        if lease:
            db.execute(update(Mission).where(Mission.id == identifier, Mission.tenant == member.tenant)
                       .values(version=Mission.version))
            member.guard(db)
        row = owned(db, Mission, identifier, member)
        if row.inputs.get("kind") != "analysis":
            raise HTTPException(404, "Analysis mission unavailable.")
        digest = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
        if row.events[-1].get("request_hash") == digest and row.events[-1].get("by") == member.subject:
            return snapshot(row)
        if body.version != row.version or row.state in ("cancelled", "verified", "no_feasible_action"):
            raise HTTPException(409, "Mission unavailable for this step.")
        result = dict(row.result)
        agent = "Decision Engine Agent"
        evidence = {"analysis_id": row.inputs["analysis_id"]}
        if body.action == "cancel":
            state, reason = "cancelled", "Staff cancelled the mission."
        elif (body.action == "advance" and row.state in ("planned","in_progress")
              and now() - datetime.fromisoformat(row.events[0]["at"]) > timedelta(days=1)):
            state, reason = "no_feasible_action", "Analysis evidence review expired. Start a fresh assessment."
        elif body.action == "advance" and row.state in ("planned", "in_progress"):
            import os
            from core.agent_planner import (
                PlanningContext,
                ToolCandidate,
                choose_next_tool,
            )

            pending = list(result["pending"])

            # Retrieve tenant-scoped evidence with bounded retry.
            for read_attempt in range(2):
                try:
                    run = get_run_by_id(
                        row.inputs["analysis_id"],
                        tenant=member.tenant,
                    )
                    break
                except OperationalError:
                    if read_attempt:
                        raise
                    evidence["read_retries"] = 1

            payload = (run or {}).get("payload") or {}

            def has_evidence(tool):
                if tool == "meter":
                    # Registration supports an inspection, not
                    # a claim of calibrated anomaly evidence.
                    return bool(row.inputs.get("device_id"))

                resource = payload.get(tool) or {}
                _, metric, _ = _ANALYSIS_TOOLS[tool]
                value = resource.get(metric)

                return (
                    resource.get("status") == "analyzed"
                    and bool(resource.get(
                        "anomaly_detection_available"
                    ))
                    and type(value) in (int, float)
                    and 0 <= value < float("inf")
                )

            candidates = [
                ToolCandidate(
                    tool=tool,
                    evidence_available=has_evidence(tool),
                    attempts=result["attempts"].get(tool, 0),
                    priority=100 if tool == "meter" else 0,
                )
                for tool in pending
                if tool in ("water", "energy", "meter")
            ]

            from core.ai_client import inference_enabled, _usage

            previous_usage = _usage.get()
            mission_usage = result.get("inference_attempts", 0)


            allow_ai = (
                inference_enabled()
                and mission_usage < 3
                and any(
                    candidate.evidence_available
                    for candidate in candidates
                )
            )

            if not allow_ai:
                candidates = [
                    candidate.model_copy(
                        update={
                            "priority": 100
                            if candidate.tool == "meter"
                            else 10 - index
                        }
                    )
                    for index, candidate in enumerate(candidates)
                ]

            evidence["planning_candidates"] = [
                candidate.model_dump(mode="json")
                for candidate in candidates
            ]

            budget_token = _usage.set(max(previous_usage, mission_usage))
            try:
                decision = choose_next_tool(
                    PlanningContext(
                        goal=row.inputs["goal"],
                        candidates=candidates,
                        findings_count=len(result["findings"]),
                    ),
                    allow_ai=allow_ai,
                )
            finally:
                consumed = max(0, _usage.get() - max(previous_usage, mission_usage))
                _usage.reset(budget_token)
                _usage.set(min(3, previous_usage + consumed))
            result["inference_attempts"] = mission_usage + consumed

            if decision.tool is None:
                raise HTTPException(
                    409,
                    "No eligible investigation remains."
                )

            key = decision.tool
            pending.remove(key)

            evidence["planner"] = decision.model_dump(
                mode="json"
            )
            if key == "meter":
                from core.telemetry import observations
                measured = observations(row.inputs["device_id"], member)
                agent = "Water Leakage Agent" if measured["metric"] == "water_counter" else "Energy Optimization Agent"
                evidence.update(device_id=measured["device"], zone=measured["zone_id"])
                result["attempts"] = {**result["attempts"], "meter":1}
                result["meter_evidence"] = {key:measured[key] for key in ("device","zone_id","calibrated","stale","findings")}
                if measured["findings"] and measured["calibrated"] and not measured["stale"]:
                    result["findings"] = [*result["findings"], {"action":"Staff inspection","source":evidence.copy(),
                                          "evidence_type":"meter_anomaly"}]
                reason = "Checked registered meter calibration, freshness and recorded anomaly evidence."
            else:
                agent, metric, unit = _ANALYSIS_TOOLS[key]
                attempts = dict(result["attempts"])
                attempts[key] = attempts.get(key, 0) + 1
                result["attempts"] = attempts
                resource = (run or {}).get("payload", {}).get(key) or {}
                evidence["field"] = key + "." + metric
                value = resource.get(metric)
                if resource.get("status") != "analyzed" or not resource.get("anomaly_detection_available"):
                    reason = "Insufficient measured time-series evidence. Try the next available domain."
                elif type(value) not in (float, int) or not 0 <= value < float("inf"):
                    reason = "Invalid stored metric. Recheck the source run."
                    if attempts[key] < 2:
                        pending.append(key)
                elif value == 0:
                    reason = "No estimated loss supports a maintenance intervention."
                else:
                    signals = resource.get("anomaly_events", [])
                    persistent = {"possible_leakage", "persistent_off_hours_load"}
                    strongest = next((signal for signal in signals if signal.get("evidence_status") in persistent),
                                     next(iter(signals), {}))
                    if strongest:
                        evidence["observation"] = {field: strongest.get(field) for field in (
                            "date", "timestamp", "location", "zone", "meter_id", "baseline_quantity", "evidence_status", "basis")}
                    action = (
                        "Inspect documented inactive-period water flow" if strongest.get("evidence_status") == "possible_leakage" else
                        "Review interval load and equipment schedules with qualified facilities staff"
                        if strongest.get("evidence_status") == "persistent_off_hours_load" else "Staff inspection"
                    )
                    result["findings"] = [*result["findings"], {"metric": metric, "value": value, "unit": unit,
                                          "source": evidence.copy(), "action": action, "evidence_type": "estimate"}]
                    reason = "Validated positive baseline excess in the stored analysis. Cause requires verification."
            result["pending"] = pending
            state = "in_progress" if pending else ("awaiting_approval" if result["findings"] else "no_feasible_action")
        elif body.action == "approve" and row.state == "awaiting_approval":
            admin(member)
            state, reason = "awaiting_verification", "Facility administrator approved a staff inspection."
        elif body.action == "verify" and row.state == "awaiting_verification" and body.evidence_ref:
            admin(member)
            if body.work_order_id:
                from core.telemetry import WorkOrder
                order = owned(db, WorkOrder, body.work_order_id, member)
                if not order.result or order.device != row.inputs.get("device_id"):
                    raise HTTPException(409, "Require reviewed maintenance evidence from the mission meter.")
                result["measured_outcome"] = {"work_order_id":order.id, "difference":order.result["measured_difference"],
                                              "unit":order.result["unit"]}
            result["inspection_evidence"] = body.evidence_ref
            state, reason = "verified", "Administrator recorded inspection evidence. Savings require comparable meter intervals."
        else:
            raise HTTPException(409, "Step requires a compatible state and evidence.")
        if lease:
            member.guard(db)
        if body.action == "cancel":
            db.execute(update(ExecutionJob).where(ExecutionJob.tenant == row.tenant,
                ExecutionJob.mission_id == row.id, ExecutionJob.status.in_(["queued","running","retry","paused"]))
                .values(status="cancelled", claim_token=None, lease_until=None, updated_at=now().isoformat()))
        events = [*row.events, event(agent, body.action, state=state, reason=reason, evidence=evidence,
                                     by=member.subject, request_hash=digest)]
        changed = db.execute(update(Mission).where(Mission.id == row.id, Mission.version == body.version)
                             .values(version=body.version+1, state=state, result=result, events=events))
        if changed.rowcount != 1:
            raise HTTPException(409, "Concurrent mission update.")
        db.commit()
        return snapshot(row)


class Transition(Input):
    version: int = Field(ge=1)
    action: Literal["replan", "approve", "reject", "cancel", "confirm_handover"]
    service_id: str | None = None
    accepted_g: Mass | None = None
    revenue_paise: Money | None = None
    costs_paise: Money | None = None
    receipt_ref: Name | None = None


@router.post("/missions/{identifier}/transitions")
def transition(identifier: str, body: Transition, member: Member = Depends(require_member)):
    with mission_inference(member, identifier=identifier):
        return _apply_transition(identifier, body, member)


def _apply_transition(identifier: str, body: Transition, member: Member):
    with Session(engine) as db:
        row = owned(db, Mission, identifier, member)
        digest = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
        if row.events[-1].get("request_hash") == digest and row.events[-1].get("by") == member.subject:
            return current_snapshot(db, row)
        if row.state in ("cancelled", "no_feasible_action", "handover_confirmed", "grouped", "inventory_split", "professional_review") or row.version != body.version:
            raise HTTPException(409, "Mission state has changed.")
        if row.inputs.get("kind"):
            raise HTTPException(409, "This endpoint requires a material mission.")
        batch = Batch(**row.inputs)
        trace = []
        result = dict(row.result)
        service_id = row.service_id
        passport = row.passport
        if body.action in ("cancel", "reject", "confirm_handover") and service_id:
            admin(member)
            release = batch.quantity_g
            if body.action == "confirm_handover":
                if not body.receipt_ref or body.accepted_g is None or body.accepted_g > release:
                    raise HTTPException(422, "Accepted mass and private receipt reference required.")
                release -= body.accepted_g
            db.execute(update(Directory).where(Directory.id == service_id, Directory.tenant == member.tenant)
                       .values(remaining_g=Directory.remaining_g + release))
        if body.action in ("confirm_handover", "reject") and row.state == "approved":
            db.add(ServiceOutcome(mission_id=row.id, service_id=service_id, offered_g=batch.quantity_g,
                                  accepted_g=body.accepted_g if body.action == "confirm_handover" else 0,
                                  rejected=int(body.action == "reject")))
        action = body.action
        if action == "approve" and row.state == "awaiting_approval":
            admin(member)
            if body.service_id not in {m["service_id"] for m in result["options"]}:
                raise HTTPException(409, "Service was not in the proposal.")
            eligible = current_snapshot(db, row)["result"]["options"]
            reserved = False
            proposal = next(m for m in result["options"] if m["service_id"] == body.service_id)
            current = next((m for m in eligible if m["service_id"] == body.service_id), None)
            terms = ("quote_paise_per_kg", "quote_expires", "net_paise", "costs_paise", "transfer",
                     "reviewed_at", "expires", "preparation", "avoided_purchase_paise", "source")
            if current and all(current.get(key) == proposal.get(key) for key in terms):
                reserved = db.execute(update(Directory).where(Directory.id == body.service_id,
                    Directory.tenant == row.tenant, Directory.status == "verified", Directory.remaining_g >= batch.quantity_g
                    ).values(remaining_g=Directory.remaining_g - batch.quantity_g)).rowcount == 1
            if reserved:
                service_id = body.service_id
            else:
                action = "replan"
                trace.append(event("Decision Engine Agent", "service_unavailable", service_id=body.service_id))

        if action == "cancel":
            state, reason = "cancelled", "Staff cancelled this mission."
        elif body.action == "confirm_handover" and row.state == "approved":
            state, reason = "handover_confirmed", "Staff confirmed recipient evidence."
            passport = uuid.uuid4().hex
            result["actual"] = body.model_dump(include={"accepted_g", "revenue_paise", "costs_paise", "receipt_ref"})
            if body.revenue_paise is not None and body.costs_paise is not None:
                result["actual"]["net_paise"] = body.revenue_paise - body.costs_paise
        elif action == "approve" and row.state == "awaiting_approval":
            state, reason = "approved", "Administrator approved and reserved the batch."
        elif (action == "replan" and row.state != "approved") or (
                body.action == "reject" and row.state in ("awaiting_approval", "approved")):
            if body.action == "reject" and row.state == "awaiting_approval":
                admin(member)
                if body.service_id not in {m["service_id"] for m in result["options"]}:
                    raise HTTPException(409, "Select a service from the current proposal.")
                service_id = body.service_id
            exhausted = sum(e["action"] in ("replan", "reject") for e in row.events) >= 4
            if service_id:
                result["excluded"] = [*result.get("excluded", []), service_id]
            service_id = None
            if exhausted:
                state, result["options"], reason = "no_feasible_action", [], "Replanning budget exhausted."
            else:
                state, result["options"], reason = options(db, member.tenant, batch, result.get("excluded", []),
                        reviewed=bool(result.get("classification")), collective_only=bool(result.get("sources")), trace=trace)
        else:
            raise HTTPException(409, "Action unavailable in current state.")
        if state in ("cancelled", "no_feasible_action"):
            for source_id in result.get("sources", []):
                source = owned(db, Mission, source_id, member)
                if source.state == "grouped":
                    source.state = "needs_evidence"
                    source.version += 1
                    source.events = [*source.events, event("Waste-to-Wealth Agent", "collective_cancelled", collective=row.id)]
        events = [*row.events, *trace, event("Decision Engine Agent", action, state=state, reason=reason,
                                     by=member.subject, request_hash=digest)]
        changed = db.execute(update(Mission).where(Mission.id == row.id, Mission.version == body.version)
                             .values(state=state, result=result, events=events, version=body.version+1,
                                     service_id=service_id, passport=passport))
        if changed.rowcount != 1:
            raise HTTPException(409, "Concurrent mission update.")
        db.commit()
        return snapshot(row)


@router.get("/passports/{token}")
def passport(token: str):
    with Session(engine) as db:
        row = db.scalar(select(Mission).where(Mission.passport == token, Mission.state == "handover_confirmed"))
        if row is None:
            raise HTTPException(404, "Passport unavailable.")
        return {"state": row.state, "accepted_g": row.result["actual"]["accepted_g"]}


class Collective(Input):
    mission_ids: list[uuid.UUID] = Field(min_length=2, max_length=50)


@router.post("/recovery/collectives")
def aggregate(body: Collective, member: Member = Depends(require_member)):
    admin(member)
    ids = sorted(str(identifier) for identifier in body.mission_ids)
    if len(set(ids)) != len(ids):
        raise HTTPException(422, "Repeated batch.")
    request_id = str(uuid.uuid5(uuid.NAMESPACE_URL, member.tenant + "/" + "/".join(ids)))
    with Session(engine) as db:
        existing = db.scalar(select(Mission).where(Mission.tenant == member.tenant, Mission.request_id == request_id))
        if existing and existing.result.get("sources") == ids:
            return current_snapshot(db, existing)
        rows = [owned(db, Mission, identifier, member) for identifier in ids]
        if any(row.inputs.get("kind") for row in rows):
            raise HTTPException(409, "Only material batches can be grouped.")
        batches = [Batch(**row.inputs) for row in rows]
        first = batches[0]
        if not first.collection_date or first.collection_date < now().date():
            raise HTTPException(422, "A current agreed collection date is required.")
        for row, batch in zip(rows, batches):
            if (row.state not in ("needs_evidence", "awaiting_approval") or not batch.collective_consent
                    or row.result.get("sources") or not compatible_lots(first, batch)):
                raise HTTPException(409, "Batches require compatible material, consent, area, date and availability.")
        quantity = sum(batch.quantity_g for batch in batches)
        if quantity > 100000000:
            raise HTTPException(422, "Combined mass exceeds the batch limit.")
        expires = [batch.supply_expires for batch in batches if batch.supply_expires]
        combined = first.model_copy(update={"quantity_g":quantity, "supply_expires":min(expires) if expires else None, "goal": "collective_recovery",
                                            "request_id": uuid.UUID(request_id)})
        state, matches, reason = options(db, member.tenant, combined)
        matches = [match for match in matches if match["pathway"] == "collective_recovery"]
        if not matches:
            raise HTTPException(409, "No current reviewed collective capacity for the combined batch.")
        mid = str(uuid.uuid4())
        for row in rows:
            changed = db.execute(update(Mission).where(Mission.id == row.id, Mission.version == row.version)
                                 .values(state="grouped", version=row.version+1,
                                         events=[*row.events, event("Waste-to-Wealth Agent", "grouped", collective=mid)]))
            if changed.rowcount != 1:
                raise HTTPException(409, "Batch allocated concurrently.")
        group = Mission(id=mid, tenant=member.tenant, request_id=request_id, inputs=combined.model_dump(mode="json"),
                        state=state, result={"sources": ids, "options": matches},
                        events=[event("Waste-to-Wealth Agent", "grouped", reason=reason, by=member.subject)])
        db.add(group)
        db.commit()
        return snapshot(group)


class PostalArea(Base):
    __tablename__ = "postal_areas"
    pin = Column(String(6), primary_key=True)
    locality = Column(String(160), nullable=False)
    provenance = Column(JSON, nullable=False)


@router.get("/postal/{pin}")
def postal_area(pin: Pin, member: Member = Depends(require_member)):
    with Session(engine) as db:
        row = db.get(PostalArea, pin)
        if row is None:
            return {"pin": pin, "locality": None, "status": "unmapped"}
        return {"pin": pin, "locality": row.locality, "status": "reviewed",
                "source_document": row.provenance["source_document"], "publication_date": row.provenance["publication_date"]}

class ProcessingEvidence(Input):
    receipt_ref: Name
    processed_g: Mass


@router.post("/missions/{identifier}/processing-evidence")
def confirm_processing(identifier: str, body: ProcessingEvidence, member: Member = Depends(require_member)):
    admin(member)
    with Session(engine) as db:
        row = owned(db, Mission, identifier, member)
        if row.state != "handover_confirmed" or body.processed_g > row.result["actual"]["accepted_g"]:
            raise HTTPException(409, "Confirmed handover and compatible processor mass required.")
        prior = row.result.get("processing_evidence")
        if prior:
            if prior == body.model_dump():
                return snapshot(row)
            raise HTTPException(409, "Processing evidence already attached.")
        if body.receipt_ref == row.result["actual"]["receipt_ref"]:
            raise HTTPException(422, "Distinct downstream processing evidence required.")
        change = db.execute(update(Mission).where(Mission.id == identifier, Mission.version == row.version)
                            .values(version=row.version+1, result={**row.result,"processing_evidence":body.model_dump()},
                                    events=[*row.events,event("Waste-to-Wealth Agent","processing_evidenced",by=member.subject)]))
        if change.rowcount != 1:
            raise HTTPException(409, "Concurrent evidence update.")
        db.commit()
        return snapshot(row)


class AbuseReport(Input):
    reason: Literal["outdated", "privacy", "misrepresentation", "unsafe"]


@router.post("/recovery/services/{identifier}/reports")
def report_service(identifier: str, body: AbuseReport, member: Member = Depends(require_member)):
    with Session(engine) as db:
        row = owned(db, Directory, identifier, member)
        entry = event("Directory", "reported", by=member.subject, reason=body.reason)
        if not any(e["action"] == "reported" and e.get("by") == member.subject and e.get("reason") == body.reason
                   for e in row.audit):
            row.audit = [*row.audit, entry]
            row.status = "pending"
            db.commit()
        return {"status": "awaiting_review"}


@router.get("/missions/{identifier}/passport.pdf")
def passport_pdf(identifier: str, member: Member = Depends(require_member)):
    from io import BytesIO
    from fastapi.responses import Response
    from reportlab.graphics import renderPDF
    from reportlab.graphics.barcode import createBarcodeDrawing
    from reportlab.pdfgen.canvas import Canvas
    with Session(engine) as db:
        row = owned(db, Mission, identifier, member)
        if not row.passport:
            raise HTTPException(409, "Confirmed handover required.")
        buffer = BytesIO()
        canvas = Canvas(buffer)
        canvas.drawString(50, 770, "RE:GEN AI material passport")
        canvas.drawString(50, 735, "Confirmed handover (grams): " + str(row.result["actual"]["accepted_g"]))
        renderPDF.draw(createBarcodeDrawing("QR", value=row.passport, width=140, height=140), canvas, 50, 540)
        canvas.drawString(50, 515, row.passport)
        canvas.save()
        return Response(buffer.getvalue(), media_type="application/pdf", headers={"Cache-Control": "no-store"})


class RelayRequest(Input):
    mission_id: uuid.UUID
    purpose: Literal["confirm_capacity", "confirm_quote", "request_onboarding"]


@router.post("/recovery/relay")
def queue_relay(body: RelayRequest, member: Member = Depends(require_member)):
    admin(member)
    with Session(engine) as db:
        row = owned(db, Mission, str(body.mission_id), member)
        if row.inputs.get("kind") == "analysis" or row.state not in ("needs_evidence", "awaiting_approval", "manual_review"):
            raise HTTPException(409, "Open material mission required.")
        if not any(e["action"] == "relay_requested" and e.get("purpose") == body.purpose for e in row.events):
            changed = db.execute(update(Mission).where(Mission.id == row.id, Mission.version == row.version)
                                 .values(version=row.version+1, events=[*row.events, event("Directory", "relay_requested",
                                         purpose=body.purpose, by=member.subject, reason="Queued for facility staff review.")]))
            if changed.rowcount != 1:
                raise HTTPException(409, "Concurrent mission update.")
            db.commit()
        return {"status": "queued_for_facility_review"}


@router.get("/recovery/relay")
def list_relay(member: Member = Depends(require_member)):
    admin(member)
    with Session(engine) as db:
        rows = db.scalars(select(Mission).where(Mission.tenant == member.tenant,
                          Mission.state.in_(["needs_evidence","awaiting_approval","manual_review"])))
        return [{"mission_id":row.id,"purpose":e["purpose"],"requested_at":e["at"]}
                for row in rows for e in row.events if e["action"] == "relay_requested"]

# Persistent analysis execution

@router.post("/analysis-missions/{identifier}/queue")
def queue_analysis(identifier: str, member: Member = Depends(require_member)):
    from core.execution_queue import enqueue

    with Session(engine) as db:
        # Lock the mission before granting a job so cancellation cannot interleave.
        db.execute(update(Mission).where(Mission.id == identifier, Mission.tenant == member.tenant)
                   .values(version=Mission.version))
        row = owned(db, Mission, identifier, member)

        if row.inputs.get("kind") != "analysis":
            raise HTTPException(404, "Analysis mission unavailable.")

        if row.state not in ("planned", "in_progress"):
            raise HTTPException(409, "Mission does not require investigation.")

        job = enqueue(db, member.tenant, identifier, member.subject)
        db.commit()
        return job


@router.get("/execution-jobs/{identifier}")
def execution_status(identifier: str, member: Member = Depends(require_member)):
    from core.execution_queue import serialize


    with Session(engine) as db:
        return serialize(owned(db, ExecutionJob, identifier, member))


@router.post("/execution-jobs/{identifier}/run")
def run_execution_job(identifier: str, member: Member = Depends(require_member)):
    return execute_investigation(member.tenant, identifier)


def execute_investigation(tenant, identifier):
    from core.execution_queue import claim_job, finish_job
    from core.ai_client import _cloud_consent, _usage, _tenant

    job = claim_job(tenant, identifier)
    if job is None:
        raise HTTPException(409, "Execution job is unavailable or already claimed.")

    token = job["claim_token"]

    member = InvestigationLease(tenant, job["mission_id"], identifier, token)
    tenant_token = _tenant.set(tenant)
    consent_token = _cloud_consent.set(False)
    usage_token = _usage.set(0)

    try:
        with Session(engine) as db:
            row = owned(db, Mission, job["mission_id"], member)
            current = snapshot(row)

        completed = 0

        for _ in range(6):
            if current["state"] not in ("planned", "in_progress"):
                break

            previous = current["version"]

            current = _analysis_step(
                job["mission_id"],
                AnalysisStep(version=previous, action="advance"),
                member,
            )

            if current["version"] <= previous:
                break

            completed += 1

        status = (
            "retry"
            if current["state"] in ("planned", "in_progress")
            else "paused" if current["state"] == "awaiting_approval" else "completed"
        )

        if not finish_job(tenant, identifier, token, status):
            raise LostLease()

        return {
            "mission": current,
            "completed_steps": completed,
            "execution_status": status,
        }

    except LostLease:
        raise HTTPException(409, "Execution lease no longer current.")
    except Exception:
        finish_job(
            member.tenant,
            identifier,
            token,
            "retry" if job["attempts"] < 3 else "failed",
            "Execution interrupted; committed checkpoints retained.",
        )
        raise HTTPException(503, "Execution paused. Retry from saved checkpoint.")

    finally:
        _cloud_consent.reset(consent_token)
        _usage.reset(usage_token)
        _tenant.reset(tenant_token)


class RecoveryRefresh(Input):
    version: int = Field(ge=1)


@router.post("/missions/{identifier}/refresh")
def refresh_recovery(
    identifier: str,
    body: RecoveryRefresh,
    member: Member = Depends(require_member),
):
    with Session(engine) as db:
        row = owned(db, Mission, identifier, member)

        if row.inputs.get("kind"):
            raise HTTPException(422, "Expected a material recovery mission.")

        if row.version != body.version:
            raise HTTPException(409, "Refresh the mission checkpoint.")

        if row.state not in ("needs_evidence", "awaiting_approval"):
            raise HTTPException(409, "Mission cannot be replanned in this state.")

        result = dict(row.result)
        refresh_count = result.get("directory_refreshes", 0)

        if refresh_count >= 10:
            raise HTTPException(409, "Facility review required before further refreshes.")

        batch = Batch(**row.inputs)
        trace = []

        # Directory refresh uses deterministic evaluation.
        # No additional cloud inference is required.
        from core.ai_client import _usage

        token = _usage.set(3)

        try:
            state, matches, reason = options(
                db,
                member.tenant,
                batch,
                result.get("excluded", []),
                reviewed=bool(result.get("classification")),
                collective_only=bool(result.get("sources")),
                trace=trace,
            )
        finally:
            _usage.reset(token)

        if state == "manual_review":
            raise HTTPException(409, "Material evidence requires facility review.")

        result["options"] = matches
        result["directory_refreshes"] = refresh_count + 1

        events = [
            *row.events,
            event(
                "Decision Engine Agent",
                "replanning_requested",
                by=member.subject,
                reason="Recheck current verified recovery opportunities.",
            ),
            *trace,
            event(
                "Waste-to-Wealth Agent",
                state,
                reason=reason,
                eligible_options=len(matches),
            ),
        ]

        changed = db.execute(
            update(Mission)
            .where(
                Mission.id == row.id,
                Mission.tenant == member.tenant,
                Mission.version == body.version,
            )
            .values(
                state=state,
                result=result,
                events=events,
                version=body.version + 1,
            )
        )

        if changed.rowcount != 1:
            db.rollback()
            raise HTTPException(409, "Concurrent mission update.")

        db.commit()
        db.refresh(row)

        return current_snapshot(db, row)
