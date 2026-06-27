# E-Commerce API - Quick Reference Guide

## Base URL

```
http://localhost:8000          # Development
https://api.fashionstore.com   # Production
```

## Common API Patterns

### 1. Authentication Flow

#### Register User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "name": "John Doe",
    "phone": "+1234567890"
  }'
```

Response:
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "subscription_tier": "free",
  "email_verified": false,
  "is_active": true,
  "created_at": "2024-06-23T12:00:00",
  "updated_at": "2024-06-23T12:00:00"
}
```

#### Login User
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 2. Product Browsing

#### List Products
```bash
# Basic listing
curl http://localhost:8000/products

# With filtering
curl "http://localhost:8000/products?category_id=1&min_price=10&max_price=100&sort_by=price&sort_order=asc&limit=20"

# Search
curl "http://localhost:8000/products?search=blue+shirt&in_stock_only=true"
```

Response:
```json
{
  "items": [
    {
      "id": 1,
      "name": "Blue T-Shirt",
      "price": 19.99,
      "stock_qty": 50,
      "rating": 4.5,
      "images": [{"url": "...", "alt_text": "..."}],
      "tags": ["apparel", "mens"],
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

#### Get Product Details
```bash
curl http://localhost:8000/products/1
```

### 3. Shopping Cart

#### Create Cart
```bash
curl -X POST http://localhost:8000/carts \
  -H "Authorization: Bearer $TOKEN"
```

#### Add Item to Cart
```bash
curl -X POST http://localhost:8000/carts/1/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 5,
    "quantity": 2,
    "variant_options": {"size": "M", "color": "blue"}
  }'
```

#### Get Cart
```bash
curl http://localhost:8000/carts/1
```

Response:
```json
{
  "id": 1,
  "user_id": 1,
  "items": [
    {
      "product_id": 5,
      "quantity": 2,
      "price": 19.99,
      "subtotal": 39.98,
      "product_name": "Blue T-Shirt",
      "variant_options": {"size": "M"}
    }
  ],
  "subtotal": 39.98,
  "tax": 4.00,
  "shipping": 0.00,
  "total": 43.98,
  "created_at": "2024-06-23T12:00:00"
}
```

#### Remove Item
```bash
curl -X DELETE http://localhost:8000/carts/1/items/0 \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Orders & Checkout

#### Create Order
```bash
curl -X POST http://localhost:8000/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": 1,
    "shipping_address": {
      "street": "123 Main St",
      "city": "New York",
      "state": "NY",
      "zip": "10001",
      "country": "USA"
    },
    "shipping_method": "standard"
  }'
```

Response:
```json
{
  "id": 1,
  "order_number": "ORD-20240623-a1b2c3d4",
  "status": "pending",
  "subtotal": 39.98,
  "tax": 4.00,
  "shipping": 10.00,
  "total": 53.98,
  "items": [...],
  "created_at": "2024-06-23T12:00:00"
}
```

#### Get Order History
```bash
curl "http://localhost:8000/orders?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Payments with Stripe

#### Create Payment Intent
```bash
curl -X POST http://localhost:8000/payments/intent \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1}'
```

Response:
```json
{
  "client_secret": "pi_xxx_secret_xxx",
  "order_id": 1,
  "amount": 53.98,
  "currency": "USD"
}
```

**Frontend (React):**
```javascript
// Use client_secret with Stripe.js
const {error, paymentIntent} = await stripe.confirmCardPayment(clientSecret, {
  payment_method: {
    card: cardElement,
    billing_details: {name: 'John Doe'}
  }
});

if (paymentIntent.status === 'succeeded') {
  // Payment successful - confirm with backend
  await fetch('/payments/confirm', {
    method: 'POST',
    headers: {'Authorization': `Bearer ${token}`},
    body: JSON.stringify({
      order_id: 1,
      payment_intent_id: paymentIntent.id
    })
  });
}
```

### 6. Product Reviews

#### Post Review
```bash
curl -X POST http://localhost:8000/products/1/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 5,
    "title": "Great product!",
    "content": "Really good quality and fast shipping."
  }'
```

#### Get Reviews
```bash
curl "http://localhost:8000/products/1/reviews?skip=0&limit=10"
```

### 7. Wishlist

#### Add to Wishlist
```bash
curl -X POST http://localhost:8000/wishlists \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 5}'
```

## Error Responses

### Standard Error Format
```json
{
  "error": "validation_error",
  "message": "Invalid request data",
  "status_code": 422,
  "timestamp": "2024-06-23T12:00:00",
  "request_id": "req_12345",
  "details": [
    {
      "field": "email",
      "message": "Invalid email address"
    }
  ]
}
```

### Common Errors

| Status Code | Error | Cause |
|----------|-------|-------|
| 400 | Bad Request | Invalid query parameters or body |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists |
| 422 | Validation Error | Invalid input data |
| 500 | Server Error | Internal server error |

## Headers

### Authentication Header
```bash
Authorization: Bearer <your_jwt_token>
```

### Common Response Headers
```
X-Request-Id: req_12345        # Correlation ID for tracking
X-Response-Time-Ms: 125        # Response time in milliseconds
Content-Type: application/json
```

## Pagination

Most list endpoints support pagination:

```bash
# Query parameters
?skip=0      # Number of items to skip (default: 0)
&limit=20    # Number of items to return (default: 20, max: 100)
```

Response includes:
```json
{
  "items": [...],
  "total": 150,       // Total count
  "skip": 0,          // Items skipped
  "limit": 20         // Items returned
}
```

## Filtering

### Product List Filters
```bash
# By category
?category_id=1

# By price
?min_price=10&max_price=100

# By stock
?in_stock_only=true

# By search
?search=blue+shirt

# Sorting
?sort_by=price&sort_order=asc
# Options: created_at, price, rating, name
```

## Rate Limiting

Default limits:
- **100 requests per 60 seconds** per IP

Response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1624444800
```

## Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "production",
  "database": "ok",
  "stripe": "ok"
}
```

## API Documentation

Interactive docs available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Webhook (Stripe)

Stripe events are delivered to:
```
POST /payments/webhook
Header: Stripe-Signature: t=<timestamp>,v1=<signature>
```

Handled events:
- `charge.succeeded` - Payment completed
- `charge.failed` - Payment failed
- `charge.refunded` - Payment refunded

## Examples by Use Case

### Complete Purchase Flow

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"..."}' \
  | jq -r '.access_token')

# 2. Create cart
CART=$(curl -s -X POST http://localhost:8000/carts \
  -H "Authorization: Bearer $TOKEN" | jq '.id')

# 3. Add items
curl -s -X POST http://localhost:8000/carts/$CART/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id":5,"quantity":2}'

# 4. Create order
ORDER=$(curl -s -X POST http://localhost:8000/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id":'$CART',
    "shipping_address":{"street":"...","city":"...","state":"...","zip":"...","country":"..."}
  }' | jq '.id')

# 5. Create payment intent
curl -s -X POST http://localhost:8000/payments/intent \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"order_id":'$ORDER'}'

# 6. Complete payment in frontend using Stripe.js
# 7. Order is now paid and ready for fulfillment
```

## Testing with cURL

### Using Environment Variables
```bash
# Set base URL
export API_URL=http://localhost:8000

# Set token
export TOKEN=<your_jwt_token>

# Make requests
curl $API_URL/products \
  -H "Authorization: Bearer $TOKEN"
```

### Pretty Print JSON
```bash
curl -s http://localhost:8000/products | jq '.'
```

## Rate Limiting Bypass for Testing

In development, increase rate limits in `.env`:
```
RATE_LIMIT_REQUESTS=10000
```

---

**Need help?** See full API docs at `/docs` or contact support@fashionstore.com
