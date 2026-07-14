"""Pydantic request schemas mirroring the Node Zod validations.

For multipart endpoints (shop, product) the JSON arrives in a `data` form field
and is parsed against these models in the router.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ─────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["CUSTOMER", "VENDOR", "ADMIN"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    oldPassword: str
    newPassword: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    id: str
    password: str


# ── Admin ────────────────────────────────────────────────────────────────────
class UpdateUserRequest(BaseModel):
    isSuspended: bool


class BlacklistShopRequest(BaseModel):
    isBlackListed: bool


class CreateCategoryRequest(BaseModel):
    name: str
    description: Optional[str] = None


class UpdateCategoryRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# ── Shop ─────────────────────────────────────────────────────────────────────
class CreateShopRequest(BaseModel):
    name: str
    description: str
    logo: Optional[str] = None


# ── Product ──────────────────────────────────────────────────────────────────
class CreateProductRequest(BaseModel):
    name: str
    description: str
    price: float = Field(ge=0)
    discount: Optional[float] = Field(default=0, ge=0)
    categoryId: str
    inventory: int = Field(ge=0)


class UpdateProductRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    discount: Optional[float] = Field(default=None, ge=0)
    inventory: Optional[int] = Field(default=None, ge=0)
    image: Optional[List[str]] = None


# ── Order ────────────────────────────────────────────────────────────────────
class OrderProductItem(BaseModel):
    productId: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)
    discount: float = Field(default=0, ge=0)


class CreateOrderRequest(BaseModel):
    vendorId: str
    totalAmount: float = Field(gt=0)
    products: List[OrderProductItem] = Field(min_length=1)


# ── Flash sale ───────────────────────────────────────────────────────────────
class CreateFlashSaleRequest(BaseModel):
    productId: str
    discount: Optional[float] = Field(default=None, ge=0, le=100)
    startTime: datetime
    endTime: datetime

    @field_validator("endTime")
    @classmethod
    def _end_after_start(cls, end: datetime, info: Any) -> datetime:
        start = info.data.get("startTime")
        if start and end <= start:
            raise ValueError("endTime must be after startTime")
        return end


class UpdateFlashSaleRequest(BaseModel):
    discount: Optional[float] = None
    startTime: Optional[datetime] = None
    endTime: Optional[datetime] = None


# ── Payment ──────────────────────────────────────────────────────────────────
class CreatePaymentIntentRequest(BaseModel):
    amount: float = Field(gt=0)


class PaymentConfirmRequest(BaseModel):
    orderId: str
    customerId: str
    amount: float = Field(gt=0)
    transactionId: Optional[str] = None
    status: Literal["PENDING", "SUCCESS", "FAILED", "REFUNDED"]
    metadata: Optional[dict] = None


# ── Follows ──────────────────────────────────────────────────────────────────
class FollowRequest(BaseModel):
    vendorId: str


# ── Reviews ──────────────────────────────────────────────────────────────────
class CreateReviewRequest(BaseModel):
    productId: str
    comment: str
    rating: int = Field(ge=0, le=5)


# ── Recent products ──────────────────────────────────────────────────────────
class RecentProductRequest(BaseModel):
    products: List[str]


# ── Chatbot ──────────────────────────────────────────────────────────────────
class ChatbotRequest(BaseModel):
    message: str
