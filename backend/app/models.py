from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Dormitory(Base):
    __tablename__ = "dormitories"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    building_number: Mapped[str] = mapped_column(String(32), unique=True)
    gender: Mapped[str] = mapped_column(String(16))
    floors: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    rooms: Mapped[list["Room"]] = relationship(back_populates="dormitory", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dormitory_id: Mapped[int] = mapped_column(ForeignKey("dormitories.id", ondelete="CASCADE"))
    floor_number: Mapped[int] = mapped_column(Integer)
    room_number: Mapped[str] = mapped_column(String(32))
    room_type: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="normal")
    dormitory: Mapped["Dormitory"] = relationship(back_populates="rooms")
    beds: Mapped[list["Bed"]] = relationship(back_populates="room", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("dormitory_id", "room_number", name="uq_room_in_dorm"),)


class Bed(Base):
    __tablename__ = "beds"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    bed_code: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="vacant")
    room: Mapped["Room"] = relationship(back_populates="beds")
    __table_args__ = (UniqueConstraint("room_id", "bed_code", name="uq_bed_code_in_room"),)


class CheckinApplication(Base):
    __tablename__ = "checkin_applications"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    applicant_name: Mapped[str] = mapped_column(String(128))
    employee_no: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CheckinRecord(Base):
    __tablename__ = "checkin_records"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    application_id: Mapped[Optional[int]] = mapped_column(ForeignKey("checkin_applications.id"), nullable=True)
    bed_id: Mapped[int] = mapped_column(ForeignKey("beds.id"))
    employee_name: Mapped[str] = mapped_column(String(128))
    employee_no: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    checkin_date: Mapped[date] = mapped_column(Date)
    deposit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    key_received: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FeeConfig(Base):
    __tablename__ = "fee_configs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_type: Mapped[str] = mapped_column(String(16), unique=True)
    monthly_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class FeeRecord(Base):
    __tablename__ = "fee_records"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    checkin_record_id: Mapped[int] = mapped_column(ForeignKey("checkin_records.id", ondelete="CASCADE"))
    billing_month: Mapped[date] = mapped_column(Date)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reminder_count: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (UniqueConstraint("checkin_record_id", "billing_month", name="uq_fee_month"),)


class SwapApplication(Base):
    __tablename__ = "swap_applications"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    checkin_record_id: Mapped[int] = mapped_column(ForeignKey("checkin_records.id"))
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_room_hint: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SwapHistory(Base):
    __tablename__ = "swap_histories"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    checkin_record_id: Mapped[int] = mapped_column(ForeignKey("checkin_records.id"))
    from_bed_id: Mapped[int] = mapped_column(Integer)
    to_bed_id: Mapped[int] = mapped_column(Integer)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    operated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CheckoutApplication(Base):
    __tablename__ = "checkout_applications"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    checkin_record_id: Mapped[int] = mapped_column(ForeignKey("checkin_records.id"))
    planned_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CheckoutRecord(Base):
    __tablename__ = "checkout_records"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    checkin_record_id: Mapped[int] = mapped_column(ForeignKey("checkin_records.id"), unique=True)
    checkout_date: Mapped[date] = mapped_column(Date)
    inspection_damage: Mapped[bool] = mapped_column(Boolean, default=False)
    damage_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deposit_refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    key_returned: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RepairOrder(Base):
    __tablename__ = "repair_orders"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    checkin_record_id: Mapped[Optional[int]] = mapped_column(ForeignKey("checkin_records.id"), nullable=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))
    category: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(Text)
    urgency: Mapped[str] = mapped_column(String(16), default="normal")
    status: Mapped[str] = mapped_column(String(16), default="open")
    assignee: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
