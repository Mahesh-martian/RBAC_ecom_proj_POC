"""
Pydantic schemas for API request/response validation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from app.models import OrderStatus


# ============= Authentication Schemas =============

class UserRegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(min_length=12, description="Min 12 characters")
    name: str = Field(min_length=2)
    phone: Optional[str] = None
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User profile response."""
    id: int
    email: str
    name: str
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    subscription_tier: str
    email_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============= Category Schemas =============

class CategoryCreate(BaseModel):
    """Create category request."""
    name: str
    slug: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryUpdate(BaseModel):
    """Update category request."""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryResponse(BaseModel):
    """Category response."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= Product Schemas =============

class ProductCreateRequest(BaseModel):
    """Create product request."""
    sku: str
    name: str
    description: Optional[str] = None
    category_id: int
    price: float = Field(gt=0)
    cost: Optional[float] = Field(default=None, ge=0)
    currency: str = "USD"
    stock_qty: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=10, ge=0)
    images: Optional[List[Dict[str, str]]] = None  # [{url, alt_text, order}, ...]
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias='metadata')


class ProductUpdateRequest(BaseModel):
    """Update product request."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0)
    cost: Optional[float] = Field(default=None, ge=0)
    stock_qty: Optional[int] = Field(default=None, ge=0)
    reorder_level: Optional[int] = Field(default=None, ge=0)
    images: Optional[List[Dict[str, str]]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias='metadata')
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """Product response."""
    id: int
    sku: str
    name: str
    description: Optional[str] = None
    category_id: int
    price: float
    cost: Optional[float] = None
    currency: str
    stock_qty: int
    reorder_level: int
    images: Optional[List[Dict[str, str]]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias='product_metadata')
    rating: float
    rating_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class ProductListParams(BaseModel):
    """Product list query parameters."""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    category_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    search: Optional[str] = None
    sort_by: str = "created_at"  # created_at, price, rating, name
    sort_order: str = "desc"  # asc, desc
    in_stock_only: bool = False


# ============= Review Schemas =============

class ReviewCreateRequest(BaseModel):
    """Create product review request."""
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = None
    content: Optional[str] = None


class ReviewResponse(BaseModel):
    """Product review response."""
    id: int
    product_id: int
    user_id: int
    rating: int
    title: Optional[str] = None
    content: Optional[str] = None
    helpful_count: int
    unhelpful_count: int
    is_verified_purchase: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= Cart Schemas =============

class CartItemRequest(BaseModel):
    """Add/update item in cart."""
    product_id: int
    quantity: int = Field(ge=1)
    variant_options: Optional[Dict[str, str]] = None


class CartItemResponse(BaseModel):
    """Cart item response."""
    product_id: int
    quantity: int
    variant_options: Optional[Dict[str, str]] = None
    price: float
    subtotal: float
    product_name: str
    product_image: Optional[str] = None


class CartResponse(BaseModel):
    """Shopping cart response."""
    id: int
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    items: List[CartItemResponse] = []
    subtotal: float
    tax: float
    shipping: float
    total: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= Order Schemas =============

class OrderCreateRequest(BaseModel):
    """Create order from cart."""
    cart_id: int
    shipping_address: Dict[str, str]  # {street, city, state, zip, country}
    shipping_method: str = "standard"  # standard, express, overnight


class OrderResponse(BaseModel):
    """Order response."""
    id: int
    order_number: str
    status: OrderStatus
    user_id: int
    
    subtotal: float
    tax: float
    shipping: float
    discount: float
    total: float
    currency: str
    
    payment_intent_id: Optional[str] = None
    payment_method: Optional[str] = None
    shipping_address: Dict[str, str]
    tracking_number: Optional[str] = None
    
    items: List[Dict[str, Any]] = []
    
    created_at: datetime
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Order list item."""
    id: int
    order_number: str
    status: OrderStatus
    total: float
    created_at: datetime
    shipped_at: Optional[datetime] = None


class OrderCancelRequest(BaseModel):
    """Cancel order request."""
    reason: Optional[str] = None


# ============= Payment Schemas =============

class PaymentIntentRequest(BaseModel):
    """Create payment intent request."""
    order_id: int


class PaymentIntentResponse(BaseModel):
    """Payment intent response."""
    client_secret: str
    order_id: int
    amount: float
    currency: str


class PaymentConfirmRequest(BaseModel):
    """Confirm payment request."""
    order_id: int
    payment_method_id: str  # From Stripe.js


class PaymentWebhookEvent(BaseModel):
    """Stripe webhook event."""
    id: str
    type: str
    data: Dict[str, Any]


# ============= Chat Schemas =============

class ChatHistoryMessage(BaseModel):
    """A prior turn supplied by the client for short-term conversational context."""
    role: str  # "user" | "bot"
    text: str = Field(min_length=1, max_length=2000)


class ChatQueryRequest(BaseModel):
    """Chat query request."""
    query: str = Field(min_length=1, max_length=500)
    product_id: Optional[int] = None
    category: Optional[str] = None
    conversation_id: Optional[str] = None
    user_name: Optional[str] = Field(default=None, max_length=120)
    user_role: Optional[str] = Field(default=None, max_length=40)
    history: List[ChatHistoryMessage] = Field(default_factory=list)


class ChatRecommendation(BaseModel):
    """Product recommendation returned by chat."""
    id: str
    name: str
    sku: Optional[str] = None
    price: float
    currency: str
    image_url: Optional[str] = None


class ChatUsage(BaseModel):
    """Azure usage metrics for a single chat/RAG response."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    retrieval_count: int = 0
    search_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    # Prompt versions used to build the answer, keyed by prompt id (or id:variant).
    # Populated by the prompt registry so responses are auditable and A/B tests
    # can be attributed to specific prompt revisions.
    prompt_versions: Dict[str, str] = Field(default_factory=dict)


class ChatQueryResponse(BaseModel):
    """Chat response payload."""
    answer: str
    recommendations: List[ChatRecommendation] = []
    citations: List[str] = []
    conversation_id: Optional[str] = None
    response_type: str = "general"  # general | policy_support | product
    provider: str = "local"  # local | azure | hybrid
    confidence: Optional[float] = None
    usage: Optional[ChatUsage] = None


class ChatProviderComparison(BaseModel):
    """Single provider result used in side-by-side chat benchmarks."""
    answer: str
    citations: List[str] = []
    provider: str
    confidence: Optional[float] = None
    latency_ms: float


class ChatComparisonResponse(BaseModel):
    """Side-by-side benchmark payload for comparing chat providers."""
    query: str
    current: ChatProviderComparison
    langchain: ChatProviderComparison


# ============= RAGAS Admin Schemas =============

class RagasRunRequest(BaseModel):
    """Body for POST /admin/rag/ragas/run.

    Every field mirrors a CLI flag on scripts/ragas_eval.py so the admin path
    stays faithful to the offline runner.
    """

    limit: Optional[int] = Field(default=None, ge=1, description="Cap on cases evaluated.")
    role: Optional[str] = Field(default=None, description="customer | vendor | admin")
    include_stretch: bool = Field(default=False, description="Also run stretch_cases.")
    skip_denied: bool = Field(default=False, description="Skip roles_denied (negative RBAC) replays.")
    dry_run: bool = Field(default=False, description="Replay only; skip RAGAS metric scoring.")
    metrics: Optional[List[str]] = Field(
        default=None,
        description=(
            "Subset of faithfulness/answer_relevancy/context_precision/"
            "context_recall/answer_similarity. Defaults to settings.ragas_metrics."
        ),
    )
    concurrency: int = Field(default=2, ge=1, le=8)
    fail_on_threshold: bool = Field(
        default=False,
        description=(
            "Mark the job failed when any replay row is below the configured "
            "threshold. Useful for a 'before deploy' quality gate."
        ),
    )

    @validator("role")
    def _validate_role(cls, value):  # noqa: N805 - pydantic v1 style is required for older pydantic
        if value is None:
            return value
        allowed = {"customer", "vendor", "admin"}
        if value.lower() not in allowed:
            raise ValueError(f"role must be one of {sorted(allowed)}")
        return value.lower()


class RagasJobSummaryResponse(BaseModel):
    """Compact representation returned by list endpoints."""

    id: str
    status: str
    submitted_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    total_cases: Optional[int] = None
    replays_expected: Optional[int] = None
    replays_completed: int = 0
    report_summary: Optional[Dict[str, Any]] = None


class RagasJobDetailResponse(RagasJobSummaryResponse):
    """Full job payload including the report body when the job is completed."""

    report_dir: Optional[str] = None
    report: Optional[Dict[str, Any]] = None


class RagasJobListResponse(BaseModel):
    jobs: List[RagasJobSummaryResponse]
    total: int


# ============= Wishlist Schemas =============

class WishlistAddRequest(BaseModel):
    """Add product to wishlist."""
    product_id: int


class WishlistResponse(BaseModel):
    """Wishlist item response."""
    id: int
    product_id: int
    product_name: str
    product_image: Optional[str] = None
    product_price: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Error Response Schemas =============

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    error: str = "validation_error"
    message: str
    status_code: int = 422
    details: List[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


# ============= Health Check Schemas =============

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str  # ok, degraded, error
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    environment: str
    database: str = "unknown"
    stripe: str = "unknown"
    rag: str = "unknown"


# ============= Analytics Schemas =============

class AnalyticsEventRequest(BaseModel):
    """Record analytics event."""
    event_type: str
    event_data: Optional[Dict[str, Any]] = None


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response."""
    total_revenue: float
    total_orders: int
    average_order_value: float
    total_customers: int
    new_customers_today: int
    conversion_rate: float
    top_products: List[Dict[str, Any]]
    recent_orders: List[OrderListResponse]
