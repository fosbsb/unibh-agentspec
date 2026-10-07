from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain import OrderStatus


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    name: str
    icon: str
    price_cents: int


class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=20)


class OrderCreate(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1)


class AdvanceIn(BaseModel):
    from_state: OrderStatus


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    name: str
    icon: str
    quantity: int
    unit_price_cents: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: str
    status: OrderStatus
    total_cents: int
    created_at: datetime
    ready_at: datetime | None
    items: list[OrderItemOut]


class PanelPreparing(BaseModel):
    id: int
    number: str


class PanelReady(BaseModel):
    id: int
    number: str
    ready_at: datetime


class PanelOut(BaseModel):
    preparing: list[PanelPreparing]
    ready: list[PanelReady]
    avg_prep_seconds: int | None
