# E-Commerce API

Production-grade e-commerce API built with FastAPI, SQLAlchemy, and Stripe integration. Full support for product catalog, shopping cart, orders, and payments.

## Features

- ✅ **Product Catalog** - Browse, search, filter products by category, price, ratings
- ✅ **Shopping Cart** - Add/remove items, persistent carts for users and guests
- ✅ **Secure Checkout** - Multi-step checkout with validation
- ✅ **Order Management** - Create, track, and manage orders
- ✅ **Stripe Payments** - Secure payment processing with webhook handling
- ✅ **User Accounts** - Registration, authentication, profile management
- ✅ **Product Reviews** - Rating and review system with verified purchase badges
- ✅ **Inventory Management** - Stock tracking with low-stock alerts
- ✅ **JWT Authentication** - Secure token-based auth with refresh tokens
- ✅ **Observability** - Structured logging, Application Insights integration
- ✅ **CORS & Security** - Production-ready security middleware

## Tech Stack

- **Framework**: FastAPI 0.115+
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0 (async)
- **Auth**: JWT tokens with bcrypt password hashing
- **Payments**: Stripe API
- **Deployment**: Docker, Azure Container Apps
- **Observability**: Application Insights, structured JSON logging

## Project Structure

```
ecom/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration management
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── db.py                   # Database session management
│   ├── dependencies.py         # FastAPI dependency injection
│   ├── routers/                # API route handlers
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── products.py        # Product catalog endpoints
│   │   ├── carts.py           # Shopping cart endpoints
│   │   ├── orders.py          # Order management endpoints
│   │   └── payments.py        # Stripe payment endpoints
│   ├── services/               # Business logic services
│   │   ├── auth.py            # User authentication
│   │   ├── product_service.py # Product operations
│   │   ├── order_service.py   # Order management
│   │   └── stripe_service.py  # Stripe integration
│   └── middleware/
│       └── telemetry.py       # Request tracking & logging
├── infra/                      # Infrastructure as Code (Bicep)
├── tests/                      # Unit and integration tests
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container image
├── docker-compose.yml          # Local development setup
├── .env.example               # Environment template
└── README.md                  # This file
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker (optional, for containerized development)

### Local Development

#### 1. Setup Environment

```bash
cd ecom

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure Database

Create `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and set:
```
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ecommerce
JWT_SECRET=your-secret-key-minimum-32-chars
STRIPE_API_KEY=sk_test_your_stripe_key
```

#### 3. Run with Docker Compose (Recommended)

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database on `localhost:5432`
- FastAPI server on `http://localhost:8000`

The API will automatically:
- Create database tables on startup
- Apply migrations
- Start listening on port 8000

#### 4. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/docs
```

### Without Docker

If running directly on your machine:

```bash
# Start PostgreSQL (must be running)
# Then run the API server:

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication

- `POST /auth/register` - Create user account
- `POST /auth/login` - Login (returns JWT tokens)
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user profile

### Products

- `GET /products` - List products (with filtering & pagination)
- `GET /products/{id}` - Get product details
- `GET /products/{id}/reviews` - Get product reviews
- `POST /products/{id}/reviews` - Post review (authenticated)
- `POST /products` - Create product (admin)
- `PATCH /products/{id}` - Update product (admin)
- `DELETE /products/{id}` - Delete product (admin)

### Shopping Cart

- `POST /carts` - Create cart
- `GET /carts/{id}` - Get cart contents
- `POST /carts/{id}/items` - Add item to cart
- `PATCH /carts/{id}/items/{index}` - Update item quantity
- `DELETE /carts/{id}/items/{index}` - Remove item from cart
- `DELETE /carts/{id}` - Clear cart

### Orders

- `POST /orders` - Create order from cart
- `GET /orders` - Get user's orders
- `GET /orders/{id}` - Get order details
- `POST /orders/{id}/cancel` - Cancel order
- `GET /orders/admin/all` - Get all orders (admin)
- `PATCH /orders/{id}/status` - Update order status (admin)
- `GET /orders/admin/stats` - Dashboard statistics (admin)

### Payments

- `POST /payments/intent` - Create Stripe PaymentIntent
- `POST /payments/confirm` - Confirm payment
- `POST /payments/webhook` - Stripe webhook endpoint
- `POST /payments/{order_id}/refund` - Request refund

### Health & Info

- `GET /health` - Health check
- `GET /info` - API information
- `GET /` - Welcome message

### RAG (Policy & Support)

- `POST /chat/query` - Unified chat endpoint (products + policy/support)
- `POST /admin/rag/index-policies` - Index local policy docs into Azure AI Search

## Azure RAG Upgrade (Azure OpenAI + Azure AI Search)

The app now supports higher-quality semantic retrieval and answer generation for policy/support questions.

### 1. Configure Azure Environment Variables

Set these values in `.env`:

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_CHAT_DEPLOYMENT`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_ADMIN_KEY`
- `AZURE_SEARCH_INDEX_NAME`
- `AZURE_SEARCH_SEMANTIC_CONFIG`
- `RAG_PROVIDER=azure` (or `hybrid` for Azure-first with local fallback)
- `RAG_MIN_LOCAL_SCORE` and `RAG_MIN_AZURE_SCORE` for retrieval confidence guardrails
- `RAG_ADMIN_API_KEY` to secure admin RAG endpoints

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start API

```bash
docker-compose up -d
```

### 4. Index Policy Documents

```bash
curl -X POST http://localhost:8000/admin/rag/index-policies \
  -H "X-Admin-Key: <your-rag-admin-api-key>"
```

Policy documents are read from the `policies/` folder and uploaded as vectorized chunks.

### 5. Query Support/Policy RAG

```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is your return policy?"}'
```

Expected behavior:
- Policy/support questions -> grounded answers with policy citations
- Shopping/product questions -> product recommendations with SKUs/images

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

(Only in development mode)

## Authentication

### JWT Token Flow

1. **Register**: `POST /auth/register` with email, password, name
2. **Login**: `POST /auth/login` with email, password
3. **Response**: Returns `access_token` and `refresh_token`
4. **Usage**: Add `Authorization: Bearer <token>` header to protected endpoints
5. **Refresh**: Use refresh token to get new access token (expires in 24h)

### Protected Endpoints

Add token to request header:
```bash
curl -H "Authorization: Bearer your_token_here" \
     http://localhost:8000/orders
```

## Environment Configuration

Key environment variables (see `.env.example` for complete list):

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | development | Environment (development, staging, production) |
| `DATABASE_URL` | - | PostgreSQL connection string |
| `JWT_SECRET` | - | Secret key for JWT signing (min 32 chars) |
| `STRIPE_API_KEY` | - | Stripe API key (sk_test_... for dev) |
| `STRIPE_WEBHOOK_SECRET` | - | Stripe webhook signing secret |
| `CORS_ORIGINS` | localhost | Allowed CORS origins |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Testing

### Unit Tests

```bash
pytest tests/
```

### Integration Tests

```bash
pytest tests/ -m integration
```

### Test Coverage

```bash
pytest --cov=app tests/
```

## Database Migrations

The database schema is automatically created/migrated on startup via SQLAlchemy.

To manually create tables:
```python
# From Python shell:
from app.db import DatabaseManager
import asyncio

async def create():
    await DatabaseManager.initialize()
    await DatabaseManager.create_tables()

asyncio.run(create())
```

## Stripe Integration

### Development (Test Mode)

Use Stripe test keys from https://dashboard.stripe.com/test/apikeys:
- **API Key**: `sk_test_...`
- **Webhook Secret**: `whsec_...`

Test card numbers:
- Visa: `4242 4242 4242 4242`
- Visa (decline): `4000 0000 0000 0002`
- Amex: `3782 822463 10005`

### Production

1. Get live keys from Stripe dashboard
2. Store in Azure Key Vault
3. Update environment variables
4. Configure webhook in Stripe dashboard pointing to `/payments/webhook`

## Deployment

### Azure Container Apps

See `infra/` directory for Bicep templates.

Quick deploy:
```bash
# Build and push image
docker build -t fashionstore-ecom:latest .
docker tag fashionstore-ecom:latest <acr>.azurecr.io/fashionstore-ecom:latest
docker push <acr>.azurecr.io/fashionstore-ecom:latest

# Deploy to Container Apps
az containerapp up --name ecommerce-api \
                   --resource-group your-rg \
                   --image <acr>.azurecr.io/fashionstore-ecom:latest
```

## Monitoring & Logging

### Application Insights

Structured JSON logging automatically captured in Application Insights.

View logs:
```bash
az monitor app-insights query \
  --app your-app-insights-name \
  --resource-group your-rg \
  --analytics-query "traces | where severity == 'error'"
```

### Local Logs

```bash
# View application logs
docker logs ecommerce-api

# Watch logs in real-time
docker logs -f ecommerce-api
```

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql postgresql://postgres:password@localhost:5432/ecommerce

# Check if service is running
docker ps | grep postgres
```

### JWT Token Errors

- Ensure `JWT_SECRET` is set and minimum 32 characters
- Token must be in `Authorization: Bearer <token>` format
- Access tokens expire after 24 hours (use refresh token)

### Stripe Webhook Issues

- Verify webhook URL is accessible from internet
- Check webhook secret matches `STRIPE_WEBHOOK_SECRET`
- Review Stripe dashboard event delivery logs

## Performance Tips

- Enable database connection pooling (configured by default)
- Use pagination (limit=20 by default)
- Add Redis caching layer for product catalog
- Use CDN for static product images
- Enable gzip compression (enabled by default)

## Security Considerations

- ✅ Passwords hashed with bcrypt (12 rounds)
- ✅ JWT tokens with expiration
- ✅ CORS restrictions
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Rate limiting available (implement in middleware)
- ✅ Stripe PCI compliance (no card data stored)
- ⚠️ Always use HTTPS in production
- ⚠️ Store secrets in Key Vault, not .env files
- ⚠️ Validate all user inputs (Pydantic schemas)

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Write tests for new functionality
3. Ensure tests pass: `pytest tests/`
4. Commit with clear message: `git commit -m "Add my feature"`
5. Push and create pull request

## License

Proprietary - Fashion Store E-Commerce Platform

## Support

For issues, questions, or contributions:
- Email: dev@fashionstore.com
- Issues: GitHub Issues
- Documentation: `/docs` endpoint

---

**Ready to deploy?** See [Azure Deployment Guide](./infra/README.md)
