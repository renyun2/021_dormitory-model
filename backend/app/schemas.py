from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DormitoryCreate(BaseModel):
    building_number: str
    gender: str = Field(pattern="^(male|female|mixed)$")
    floors: int = Field(ge=1, le=30)


class DormitoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    building_number: str
    gender: str
    floors: int
    created_at: datetime


class RoomCreate(BaseModel):
    dormitory_id: int
    floor_number: int
    room_number: str
    room_type: str = Field(pattern="^(single|quad|six)$")
    status: str = Field(default="normal", pattern="^(normal|maintenance)$")


class RoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dormitory_id: int
    floor_number: int
    room_number: str
    room_type: str
    status: str


class BedRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    room_id: int
    bed_code: str
    status: str


class BedWithOccupancy(BaseModel):
    bed_id: int
    bed_code: str
    bed_status: str
    occupant: Optional[str] = None
    checkin_id: Optional[int] = None


class RoomOccupancy(BaseModel):
    room_id: int
    room_number: str
    room_type: str
    room_status: str
    beds: list[BedWithOccupancy]


class CheckinAppCreate(BaseModel):
    applicant_name: str
    employee_no: Optional[str] = None
    reason: Optional[str] = None
    expected_date: Optional[date] = None


class CheckinAppRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    applicant_name: str
    employee_no: Optional[str]
    reason: Optional[str]
    expected_date: Optional[date]
    status: str
    created_at: datetime


class CheckinRecordCreate(BaseModel):
    """管理员直接录入入住（可无申请）。"""

    bed_id: int
    employee_name: str
    employee_no: Optional[str] = None
    checkin_date: date
    deposit_amount: Decimal = Decimal("0")
    key_received: bool = False
    application_id: Optional[int] = None


class CheckinFromApp(BaseModel):
    application_id: int
    bed_id: int
    checkin_date: date
    deposit_amount: Decimal = Decimal("0")
    key_received: bool = False


class CheckinRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: Optional[int]
    bed_id: int
    employee_name: str
    employee_no: Optional[str]
    checkin_date: date
    deposit_amount: Decimal
    key_received: bool
    status: str
    created_at: datetime


class StatusBody(BaseModel):
    status: str


class SwapAppCreate(BaseModel):
    checkin_record_id: int
    reason: Optional[str] = None
    expected_room_hint: Optional[str] = None


class SwapExecute(BaseModel):
    swap_application_id: int
    target_bed_id: int


class SwapHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    checkin_record_id: int
    from_bed_id: int
    to_bed_id: int
    reason: Optional[str]
    operated_at: datetime


class CheckoutAppCreate(BaseModel):
    checkin_record_id: int
    planned_date: date
    reason: Optional[str] = None


class CheckoutComplete(BaseModel):
    checkout_application_id: int
    checkout_date: date
    inspection_damage: bool = False
    damage_notes: Optional[str] = None
    deposit_refund_amount: Decimal
    key_returned: bool = False


class FeeConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    room_type: str
    monthly_rate: Decimal


class FeeConfigUpdate(BaseModel):
    monthly_rate: Decimal


class GenerateMonthFees(BaseModel):
    year: int = Field(ge=2020, le=2100)
    month: int = Field(ge=1, le=12)


class FeeRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    checkin_record_id: int
    billing_month: date
    amount_due: Decimal
    amount_paid: Decimal
    paid_at: Optional[datetime]
    reminder_count: int


class FeePayment(BaseModel):
    amount: Decimal


class RepairResidentCreate(BaseModel):
    category: str = Field(
        pattern="^(water_electric|door_window|bed|aircon|daily|other)$"
    )
    description: str
    urgency: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class RepairCreate(BaseModel):
    room_id: int
    category: str = Field(
        pattern="^(water_electric|door_window|bed|aircon|daily|other)$"
    )
    description: str
    urgency: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class RepairAssign(BaseModel):
    assignee: str
    status: str = Field(default="assigned", pattern="^(assigned|in_progress)$")


class RepairComplete(BaseModel):
    rating: int = Field(ge=1, le=5)


class RepairRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    checkin_record_id: Optional[int]
    room_id: int
    category: str
    description: str
    urgency: str
    status: str
    assignee: Optional[str]
    completed_at: Optional[datetime]
    rating: Optional[int]
    created_at: datetime


class MonthlySummaryRow(BaseModel):
    month: int
    amount_due: Decimal
    amount_paid: Decimal


class MonthlySummary(BaseModel):
    year: int
    rows: list[MonthlySummaryRow]
