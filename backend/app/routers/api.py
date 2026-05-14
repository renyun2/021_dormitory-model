from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.database import get_db
from app import schemas
from app.models import (
    Bed,
    CheckinApplication,
    CheckinRecord,
    CheckoutApplication,
    CheckoutRecord,
    Dormitory,
    FeeConfig,
    FeeRecord,
    RepairOrder,
    Room,
    SwapApplication,
    SwapHistory,
)

router = APIRouter(tags=["api"])


@router.get("/dormitories", response_model=list[schemas.DormitoryRead])
async def list_dormitories(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(Dormitory).order_by(Dormitory.id))
    return list(rows.all())


@router.post("/dormitories", response_model=schemas.DormitoryRead)
async def create_dormitory(body: schemas.DormitoryCreate, db: AsyncSession = Depends(get_db)):
    d = Dormitory(building_number=body.building_number, gender=body.gender, floors=body.floors)
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return d


@router.get("/dormitories/{dorm_id}", response_model=schemas.DormitoryRead)
async def get_dormitory(dorm_id: int, db: AsyncSession = Depends(get_db)):
    d = await db.get(Dormitory, dorm_id)
    if not d:
        raise HTTPException(status_code=404, detail="宿舍楼不存在")
    return d


@router.get("/rooms", response_model=list[schemas.RoomRead])
async def list_rooms(dormitory_id: int | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Room).order_by(Room.dormitory_id, Room.floor_number, Room.room_number)
    if dormitory_id is not None:
        q = q.where(Room.dormitory_id == dormitory_id)
    rows = await db.scalars(q)
    return list(rows.all())


def _bed_count(room_type: str) -> int:
    return {"single": 1, "quad": 4, "six": 6}.get(room_type, 1)


@router.post("/rooms", response_model=schemas.RoomRead)
async def create_room(body: schemas.RoomCreate, db: AsyncSession = Depends(get_db)):
    d = await db.get(Dormitory, body.dormitory_id)
    if not d:
        raise HTTPException(status_code=400, detail="宿舍楼不存在")
    room = Room(
        dormitory_id=body.dormitory_id,
        floor_number=body.floor_number,
        room_number=body.room_number,
        room_type=body.room_type,
        status=body.status,
    )
    db.add(room)
    await db.flush()
    n = _bed_count(body.room_type)
    for i in range(1, n + 1):
        db.add(Bed(room_id=room.id, bed_code=f"{body.room_number}-{i}", status="vacant"))
    await db.commit()
    await db.refresh(room)
    return room


@router.get("/beds", response_model=list[schemas.BedRead])
async def list_beds(room_id: int | None = None, status: str | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Bed).order_by(Bed.room_id, Bed.id)
    if room_id is not None:
        q = q.where(Bed.room_id == room_id)
    if status is not None:
        q = q.where(Bed.status == status)
    rows = await db.scalars(q)
    return list(rows.all())


@router.get("/dormitories/{dorm_id}/occupancy", response_model=list[schemas.RoomOccupancy])
async def dormitory_occupancy(dorm_id: int, db: AsyncSession = Depends(get_db)):
    d = await db.get(Dormitory, dorm_id)
    if not d:
        raise HTTPException(status_code=404, detail="宿舍楼不存在")
    cr = aliased(CheckinRecord)
    q: Select[tuple[Room, Bed, str | None, int | None]] = (
        select(Room, Bed, cr.employee_name, cr.id)
        .join(Bed, Bed.room_id == Room.id)
        .outerjoin(
            cr,
            and_(cr.bed_id == Bed.id, cr.status == "active"),
        )
        .where(Room.dormitory_id == dorm_id)
        .order_by(Room.floor_number, Room.room_number, Bed.id)
    )
    rows = (await db.execute(q)).all()
    by_room: dict[int, schemas.RoomOccupancy] = {}
    for rm, bd, emp, cid in rows:
        if rm.id not in by_room:
            by_room[rm.id] = schemas.RoomOccupancy(
                room_id=rm.id,
                room_number=rm.room_number,
                room_type=rm.room_type,
                room_status=rm.status,
                beds=[],
            )
        by_room[rm.id].beds.append(
            schemas.BedWithOccupancy(
                bed_id=bd.id,
                bed_code=bd.bed_code,
                bed_status=bd.status,
                occupant=emp,
                checkin_id=cid,
            )
        )
    return sorted(by_room.values(), key=lambda x: x.room_number)


@router.get("/checkin-applications", response_model=list[schemas.CheckinAppRead])
async def list_checkin_apps(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(CheckinApplication).order_by(CheckinApplication.id.desc()))
    return list(rows.all())


@router.post("/checkin-applications", response_model=schemas.CheckinAppRead)
async def create_checkin_app(body: schemas.CheckinAppCreate, db: AsyncSession = Depends(get_db)):
    a = CheckinApplication(
        applicant_name=body.applicant_name,
        employee_no=body.employee_no,
        reason=body.reason,
        expected_date=body.expected_date,
        status="pending",
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a


@router.patch("/checkin-applications/{app_id}/status", response_model=schemas.CheckinAppRead)
async def set_checkin_app_status(app_id: int, body: schemas.StatusBody, db: AsyncSession = Depends(get_db)):
    allowed = {"pending", "approved", "rejected", "cancelled"}
    if body.status not in allowed:
        raise HTTPException(status_code=400, detail=f"非法状态，允许: {allowed}")
    app_row = await db.get(CheckinApplication, app_id)
    if not app_row:
        raise HTTPException(status_code=404, detail="申请不存在")
    app_row.status = body.status
    await db.commit()
    await db.refresh(app_row)
    return app_row


async def _assert_bed_vacant(db: AsyncSession, bed_id: int) -> Bed:
    bed = await db.get(Bed, bed_id)
    if not bed:
        raise HTTPException(status_code=400, detail="床位不存在")
    if bed.status != "vacant":
        raise HTTPException(status_code=400, detail="床位非空闲不可分配")
    return bed


async def _assert_no_active_on_bed(db: AsyncSession, bed_id: int) -> None:
    q = await db.scalar(select(CheckinRecord.id).where(CheckinRecord.bed_id == bed_id, CheckinRecord.status == "active"))
    if q is not None:
        raise HTTPException(status_code=400, detail="该床位已有在住记录")


@router.post("/checkin-records", response_model=schemas.CheckinRecordRead)
async def create_checkin_record(body: schemas.CheckinRecordCreate, db: AsyncSession = Depends(get_db)):
    await _assert_no_active_on_bed(db, body.bed_id)
    bed = await _assert_bed_vacant(db, body.bed_id)
    rec = CheckinRecord(
        application_id=body.application_id,
        bed_id=body.bed_id,
        employee_name=body.employee_name,
        employee_no=body.employee_no,
        checkin_date=body.checkin_date,
        deposit_amount=body.deposit_amount,
        key_received=body.key_received,
        status="active",
    )
    db.add(rec)
    bed.status = "occupied"
    await db.commit()
    await db.refresh(rec)
    return rec


@router.post("/checkin-records/from-application", response_model=schemas.CheckinRecordRead)
async def checkin_from_application(body: schemas.CheckinFromApp, db: AsyncSession = Depends(get_db)):
    app_row = await db.get(CheckinApplication, body.application_id)
    if not app_row or app_row.status != "approved":
        raise HTTPException(status_code=400, detail="入住申请不存在或未批准")
    await _assert_no_active_on_bed(db, body.bed_id)
    bed = await _assert_bed_vacant(db, body.bed_id)
    rec = CheckinRecord(
        application_id=body.application_id,
        bed_id=body.bed_id,
        employee_name=app_row.applicant_name,
        employee_no=app_row.employee_no,
        checkin_date=body.checkin_date,
        deposit_amount=body.deposit_amount,
        key_received=body.key_received,
        status="active",
    )
    db.add(rec)
    bed.status = "occupied"
    await db.commit()
    await db.refresh(rec)
    return rec


@router.get("/checkin-records/active", response_model=list[schemas.CheckinRecordRead])
async def active_checkins(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(CheckinRecord).where(CheckinRecord.status == "active").order_by(CheckinRecord.id))
    return list(rows.all())


@router.get("/checkin-records/all", response_model=list[schemas.CheckinRecordRead])
async def all_checkins(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(CheckinRecord).order_by(CheckinRecord.id.desc()).limit(500))
    return list(rows.all())


@router.post("/swap-applications")
async def create_swap_application(body: schemas.SwapAppCreate, db: AsyncSession = Depends(get_db)):
    rec = await db.get(CheckinRecord, body.checkin_record_id)
    if not rec or rec.status != "active":
        raise HTTPException(status_code=400, detail="仅对在住记录提交调换申请")
    s = SwapApplication(
        checkin_record_id=body.checkin_record_id,
        reason=body.reason,
        expected_room_hint=body.expected_room_hint,
        status="pending",
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return {"id": s.id, "status": s.status, "created_at": s.created_at}


@router.get("/swap-applications")
async def list_swap_applications(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(SwapApplication).order_by(SwapApplication.id.desc()).limit(200))
    out = []
    for r in rows:
        out.append(
            {
                "id": r.id,
                "checkin_record_id": r.checkin_record_id,
                "reason": r.reason,
                "expected_room_hint": r.expected_room_hint,
                "status": r.status,
                "created_at": r.created_at,
            }
        )
    return out


@router.patch("/swap-applications/{sid}/status", response_model=dict)
async def swap_app_status(sid: int, body: schemas.StatusBody, db: AsyncSession = Depends(get_db)):
    if body.status not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="无效状态")
    row = await db.get(SwapApplication, sid)
    if not row:
        raise HTTPException(status_code=404, detail="不存在")
    row.status = body.status
    await db.commit()
    await db.refresh(row)
    return {"id": row.id, "status": row.status}


@router.post("/swap-applications/execute", response_model=schemas.CheckinRecordRead)
async def execute_swap(body: schemas.SwapExecute, db: AsyncSession = Depends(get_db)):
    sa_row = await db.get(SwapApplication, body.swap_application_id)
    if not sa_row or sa_row.status != "approved":
        raise HTTPException(status_code=400, detail="调换申请不存在或未审批通过")
    rec = await db.get(CheckinRecord, sa_row.checkin_record_id)
    if not rec or rec.status != "active":
        raise HTTPException(status_code=400, detail="在住记录无效")
    if rec.bed_id == body.target_bed_id:
        raise HTTPException(status_code=400, detail="目标床位与当前床位相同")
    tgt = await db.get(Bed, body.target_bed_id)
    if not tgt or tgt.status != "vacant":
        raise HTTPException(status_code=400, detail="目标床位不可用")
    await _assert_no_active_on_bed(db, body.target_bed_id)
    old_bed = await db.get(Bed, rec.bed_id)
    assert old_bed
    hist = SwapHistory(
        checkin_record_id=rec.id,
        from_bed_id=old_bed.id,
        to_bed_id=tgt.id,
        reason=sa_row.reason,
    )
    db.add(hist)
    old_bed.status = "vacant"
    tgt.status = "occupied"
    rec.bed_id = tgt.id
    await db.commit()
    await db.refresh(rec)
    return rec


@router.get("/swap-histories", response_model=list[schemas.SwapHistoryRead])
async def list_swap_histories(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(SwapHistory).order_by(SwapHistory.id.desc()).limit(200))
    return list(rows.all())


@router.post("/checkout-applications")
async def create_checkout_app(body: schemas.CheckoutAppCreate, db: AsyncSession = Depends(get_db)):
    rec = await db.get(CheckinRecord, body.checkin_record_id)
    if not rec or rec.status != "active":
        raise HTTPException(status_code=400, detail="无效的入住记录")
    c = CheckoutApplication(
        checkin_record_id=body.checkin_record_id,
        planned_date=body.planned_date,
        reason=body.reason,
        status="pending",
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return {"id": c.id, "status": c.status}


@router.get("/checkout-applications")
async def list_checkout_apps(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(CheckoutApplication).order_by(CheckoutApplication.id.desc()).limit(200))
    out = []
    for r in rows:
        out.append(
            {
                "id": r.id,
                "checkin_record_id": r.checkin_record_id,
                "planned_date": r.planned_date,
                "reason": r.reason,
                "status": r.status,
                "created_at": r.created_at,
            }
        )
    return out


@router.patch("/checkout-applications/{cid}/status")
async def set_checkout_app_status(cid: int, body: schemas.StatusBody, db: AsyncSession = Depends(get_db)):
    allowed = {"pending", "approved", "done", "rejected"}
    if body.status not in allowed:
        raise HTTPException(status_code=400, detail="无效状态")
    row = await db.get(CheckoutApplication, cid)
    if not row:
        raise HTTPException(status_code=404, detail="不存在")
    row.status = body.status
    await db.commit()
    return {"ok": True}


@router.post("/checkout-applications/complete")
async def complete_checkout(body: schemas.CheckoutComplete, db: AsyncSession = Depends(get_db)):
    app_row = await db.get(CheckoutApplication, body.checkout_application_id)
    if not app_row:
        raise HTTPException(status_code=404, detail="退住申请不存在")
    if app_row.status not in {"approved"}:
        raise HTTPException(status_code=400, detail="请先审批通过退住申请")
    rec = await db.get(CheckinRecord, app_row.checkin_record_id)
    if not rec or rec.status != "active":
        raise HTTPException(status_code=400, detail="入住记录不可退住")
    existing = await db.scalar(select(CheckoutRecord.id).where(CheckoutRecord.checkin_record_id == rec.id))
    if existing:
        raise HTTPException(status_code=400, detail="已完成退住")
    bed = await db.get(Bed, rec.bed_id)
    if bed:
        bed.status = "vacant"
    rec.status = "checked_out"
    app_row.status = "done"
    cr = CheckoutRecord(
        checkin_record_id=rec.id,
        checkout_date=body.checkout_date,
        inspection_damage=body.inspection_damage,
        damage_notes=body.damage_notes,
        deposit_refund_amount=body.deposit_refund_amount,
        key_returned=body.key_returned,
    )
    db.add(cr)
    await db.commit()
    await db.refresh(cr)
    return {"checkout_record_id": cr.id}


@router.get("/fee-configs", response_model=list[schemas.FeeConfigRead])
async def list_fee_configs(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(FeeConfig).order_by(FeeConfig.id))
    return list(rows.all())


@router.put("/fee-configs/{room_type}", response_model=schemas.FeeConfigRead)
async def upsert_fee_config(room_type: str, body: schemas.FeeConfigUpdate, db: AsyncSession = Depends(get_db)):
    row = await db.scalar(select(FeeConfig).where(FeeConfig.room_type == room_type))
    if not row:
        row = FeeConfig(room_type=room_type, monthly_rate=body.monthly_rate)
        db.add(row)
    else:
        row.monthly_rate = body.monthly_rate
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/fee-records/generate-month")
async def generate_month_fees(body: schemas.GenerateMonthFees, db: AsyncSession = Depends(get_db)):
    month_start = date(body.year, body.month, 1)
    cfg_rows = await db.scalars(select(FeeConfig))
    cfg = {c.room_type: c.monthly_rate for c in cfg_rows}
    ck_rows = (
        (
            await db.execute(
                select(CheckinRecord, Room.room_type)
                .join(Bed, CheckinRecord.bed_id == Bed.id)
                .join(Room, Bed.room_id == Room.id)
                .where(CheckinRecord.status == "active")
            )
        )
        .all()
    )
    created = 0
    for rec, room_type in ck_rows:
        rate = cfg.get(room_type)
        if rate is None:
            continue
        exists = await db.scalar(
            select(FeeRecord.id).where(FeeRecord.checkin_record_id == rec.id, FeeRecord.billing_month == month_start)
        )
        if exists:
            continue
        db.add(FeeRecord(checkin_record_id=rec.id, billing_month=month_start, amount_due=rate))
        created += 1
    await db.commit()
    return {"billing_month": month_start.isoformat(), "created_rows": created}


@router.get("/fee-records", response_model=list[schemas.FeeRecordRead])
async def list_fee_records(
    checkin_record_id: int | None = None,
    arrears_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    q = select(FeeRecord).order_by(FeeRecord.billing_month.desc(), FeeRecord.id.desc()).limit(1000)
    if checkin_record_id is not None:
        q = q.where(FeeRecord.checkin_record_id == checkin_record_id)
    if arrears_only:
        q = q.where(FeeRecord.amount_paid < FeeRecord.amount_due)
    rows = await db.scalars(q)
    return list(rows.all())


@router.post("/fee-records/{fid}/payment", response_model=schemas.FeeRecordRead)
async def pay_fee(fid: int, body: schemas.FeePayment, db: AsyncSession = Depends(get_db)):
    row = await db.get(FeeRecord, fid)
    if not row:
        raise HTTPException(status_code=404, detail="账单不存在")
    row.amount_paid = row.amount_paid + body.amount
    if row.amount_paid >= row.amount_due:
        row.paid_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/fee-records/{fid}/remind")
async def remind_fee(fid: int, db: AsyncSession = Depends(get_db)):
    row = await db.get(FeeRecord, fid)
    if not row:
        raise HTTPException(status_code=404, detail="账单不存在")
    if row.amount_paid >= row.amount_due:
        raise HTTPException(status_code=400, detail="已缴清无需提醒")
    row.reminder_count = (row.reminder_count or 0) + 1
    await db.commit()
    return {"reminder_count": row.reminder_count}


@router.get("/fee-records/year-summary", response_model=schemas.MonthlySummary)
async def year_summary(year: int, db: AsyncSession = Depends(get_db)):
    q = (
        select(
            func.extract("month", FeeRecord.billing_month).label("m"),
            func.coalesce(func.sum(FeeRecord.amount_due), 0),
            func.coalesce(func.sum(FeeRecord.amount_paid), 0),
        )
        .where(func.extract("year", FeeRecord.billing_month) == year)
        .group_by(func.extract("month", FeeRecord.billing_month))
        .order_by(func.extract("month", FeeRecord.billing_month))
    )
    rows = (await db.execute(q)).all()
    agg: dict[int, tuple[Decimal, Decimal]] = {int(r[0]): (Decimal(str(r[1])), Decimal(str(r[2]))) for r in rows}
    out_rows = []
    for m in range(1, 13):
        due, paid = agg.get(m, (Decimal("0"), Decimal("0")))
        out_rows.append(schemas.MonthlySummaryRow(month=m, amount_due=due, amount_paid=paid))
    return schemas.MonthlySummary(year=year, rows=out_rows)


@router.get("/repair-orders", response_model=list[schemas.RepairRead])
async def list_repairs(status: str | None = None, db: AsyncSession = Depends(get_db)):
    q = select(RepairOrder).order_by(RepairOrder.id.desc()).limit(500)
    if status:
        q = q.where(RepairOrder.status == status)
    rows = await db.scalars(q)
    return list(rows.all())


async def _room_for_checkin(db: AsyncSession, checkin_record_id: int) -> Room:
    row = (
        await db.execute(
            select(Room)
            .join(Bed, Bed.room_id == Room.id)
            .join(CheckinRecord, CheckinRecord.bed_id == Bed.id)
            .where(CheckinRecord.id == checkin_record_id, CheckinRecord.status == "active")
        )
    ).first()
    if not row:
        raise HTTPException(status_code=400, detail="未找到在住记录对应房间")
    return row[0]


@router.post("/repair-orders/by-resident", response_model=schemas.RepairRead)
async def create_repair_by_resident(
    checkin_record_id: int,
    body: schemas.RepairResidentCreate,
    db: AsyncSession = Depends(get_db),
):
    rec = await db.get(CheckinRecord, checkin_record_id)
    if not rec or rec.status != "active":
        raise HTTPException(status_code=400, detail="无效住户")
    rm2 = await _room_for_checkin(db, checkin_record_id)
    room_id = rm2.id
    ro = RepairOrder(
        checkin_record_id=checkin_record_id,
        room_id=room_id,
        category=body.category,
        description=body.description,
        urgency=body.urgency,
        status="open",
    )
    db.add(ro)
    await db.commit()
    await db.refresh(ro)
    return ro


@router.post("/repair-orders", response_model=schemas.RepairRead)
async def create_repair_admin(body: schemas.RepairCreate, db: AsyncSession = Depends(get_db)):
    room_id = body.room_id
    rm = await db.get(Room, room_id)
    if not rm:
        raise HTTPException(status_code=400, detail="房间不存在")
    ro = RepairOrder(
        checkin_record_id=None,
        room_id=room_id,
        category=body.category,
        description=body.description,
        urgency=body.urgency,
        status="open",
    )
    db.add(ro)
    await db.commit()
    await db.refresh(ro)
    return ro


@router.patch("/repair-orders/{rid}/assign", response_model=schemas.RepairRead)
async def assign_repair(rid: int, body: schemas.RepairAssign, db: AsyncSession = Depends(get_db)):
    row = await db.get(RepairOrder, rid)
    if not row:
        raise HTTPException(status_code=404, detail="工单不存在")
    row.assignee = body.assignee
    row.status = body.status
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/repair-orders/{rid}/complete", response_model=schemas.RepairRead)
async def complete_repair(rid: int, body: schemas.RepairComplete, db: AsyncSession = Depends(get_db)):
    row = await db.get(RepairOrder, rid)
    if not row:
        raise HTTPException(status_code=404, detail="工单不存在")
    row.status = "done"
    row.completed_at = datetime.now(timezone.utc)
    row.rating = body.rating
    await db.commit()
    await db.refresh(row)
    return row