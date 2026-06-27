# Phase 3: Local Testing Guide

Complete step-by-step testing of backend API + frontend integration.

## Prerequisites

- Docker & Docker Compose installed
- Node.js 16+ and npm installed
- Terminal/PowerShell access
- `curl` or Postman for API testing

## Step 1: Start Backend (Docker)

```bash
cd ecom
docker-compose up
```

**Expected Output:**
```
ecommerce-db | PostgreSQL 15.x started
ecommerce-api | INFO:     Application startup complete [startup event]
ecommerce-api | INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Wait for 30 seconds** for database migrations to complete.

### Verify Backend Health

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "development",
  "database": "ok",
  "stripe": "ok"
}
```

## Step 2: Start Frontend (React Dev Server)

In a **new terminal**:

```bash
cd ecom/frontend
npm install
npm run dev
```

**Expected Output:**
```
  VITE v5.1.7  ready in 245 ms

  ➜  Local:   http://localhost:3000/
  ➜  press h + enter to show help
```

## Step 3: Test API Endpoints

### 3.1 User Registration

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "name": "Test User",
    "phone": "+1234567890"
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "email": "test@example.com",
  "name": "Test User",
  "subscription_tier": "free",
  "email_verified": false,
  "is_active": true,
  "created_at": "2026-06-23T...",
  "updated_at": "2026-06-23T..."
}
```

### 3.2 User Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Save the `access_token` for next tests:**
```bash
export TOKEN="<your_access_token_here>"
```

### 3.3 Get User Profile

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "id": 1,
  "email": "test@example.com",
  "name": "Test User",
  "subscription_tier": "free"
}
```

### 3.4 List Products

```bash
curl http://localhost:8000/products
```

**Expected Response:** Empty array (no products seeded yet)
```json
{
  "items": [],
  "total": 0,
  "skip": 0,
  "limit": 20
}
```

### 3.5 Create Product (Admin)

```bash
curl -X POST http://localhost:8000/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "TSH-001",
    "name": "Blue T-Shirt",
    "description": "Classic blue cotton t-shirt",
    "category_id": 1,
    "price": 19.99,
    "cost": 8.50,
    "currency": "USD",
    "stock_qty": 100,
    "reorder_level": 10,
    "images": [
      {
        "url": "https://example.com/tsh-001-blue.jpg",
        "alt_text": "Blue T-Shirt Front View"
      }
    ],
    "tags": ["apparel", "mens", "cotton"],
    "metadata": {
      "color": "blue",
      "size": "M",
      "material": "100% Cotton"
    }
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "sku": "TSH-001",
  "name": "Blue T-Shirt",
  "price": 19.99,
  "stock_qty": 100,
  "rating": 0.0,
  "rating_count": 0,
  "is_active": true,
  "created_at": "2026-06-23T..."
}
```

### 3.6 Create Cart

```bash
curl -X POST http://localhost:8000/carts \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "id": "abc123def456",
  "user_id": 1,
  "items": [],
  "subtotal": 0,
  "tax": 0,
  "shipping": 0,
  "total": 0,
  "created_at": "2026-06-23T..."
}
```

**Save the `id` for next tests:**
```bash
export CART_ID="<your_cart_id_here>"
```

### 3.7 Add Item to Cart

```bash
curl -X POST http://localhost:8000/carts/$CART_ID/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2
  }'
```

**Expected Response:**
```json
{
  "id": "abc123def456",
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "price": 19.99,
      "subtotal": 39.98,
      "product_name": "Blue T-Shirt"
    }
  ],
  "subtotal": 39.98,
  "tax": 4.00,
  "shipping": 10.00,
  "total": 53.98
}
```

### 3.8 Get Cart

```bash
curl http://localhost:8000/carts/$CART_ID \
  -H "Authorization: Bearer $TOKEN"
```

**Should return cart with items**

## Step 4: Test Frontend Interface

Open **http://localhost:3000** in your browser:

### 4.1 Homepage
- ✅ Should load without errors
- ✅ See "Featured Products" section
- ✅ See category cards (Apparel, Accessories, Footwear)

### 4.2 Product Listing (/products)
- Click "Shop" in header or go to http://localhost:3000/products
- ✅ Should show product list (currently empty if no products seeded)
- ✅ Filters visible (search, price range, sort)

### 4.3 User Authentication
- Click "Register" in top right
- Fill form:
  - Email: `react@example.com`
  - Password: `ReactTest123!`
  - Name: `React Tester`
- Click "Create Account"
- ✅ Should redirect to home page
- ✅ Header should show "React Tester" (logged in)

### 4.4 Product Detail
- From product list, click on a product card
- ✅ Should show product image, name, price, rating, reviews
- ✅ Should have quantity selector and "Add to Cart" button

### 4.5 Shopping Cart
- Add product to cart from detail page
- Click cart icon (🛒) in header
- ✅ Should show cart with items
- ✅ Should show quantity controls
- ✅ Should show order summary (subtotal, tax, shipping, total)
- ✅ Should have "Proceed to Checkout" button

### 4.6 Checkout
- Click "Proceed to Checkout"
- ✅ Should show shipping address form
- Fill shipping address
- ✅ Payment form placeholder appears
- ✅ Order summary visible on right side

### 4.7 Chat Widget
- Should see floating chat button in bottom-right corner (💬)
- Click to open chat
- ✅ Chat modal opens
- ✅ Type a message (e.g., "What products do you have?")
- ✅ Should show message in chat (placeholder response for now)

## Step 5: API-Frontend Integration Test

### 5.1 Test Token Persistence
1. Login in frontend
2. Open browser DevTools → Application → Local Storage
3. ✅ Should see `auth-storage` with token and user data

### 5.2 Test API Error Handling
- Try creating account with invalid email (e.g., "notanemail")
- ✅ Should show error message from API

### 5.3 Test Cart Sync
- Add items in frontend
- Open DevTools → Application → Local Storage
- ✅ Should see `cart-storage` with cart data

## Step 6: Database Verification

In a **new terminal**, connect to PostgreSQL:

```bash
docker exec -it ecommerce-db psql -U ecom_user -d ecommerce
```

**Inside PostgreSQL:**
```sql
-- Check users
SELECT id, email, name FROM users;

-- Check products
SELECT id, sku, name, price, stock_qty FROM products;

-- Check carts
SELECT id, user_id, items FROM carts;

-- Check cart items count
SELECT COUNT(*) FROM carts WHERE user_id = 1;

-- Exit
\q
```

**Expected Results:**
- ✅ One user created (`test@example.com`)
- ✅ One product created (`TSH-001`)
- ✅ One cart created
- ✅ Cart has items

## Step 7: Logs Inspection

### Backend Logs
```bash
docker logs ecommerce-api --tail=100 -f
```

**Should see:**
- ✅ Startup logs
- ✅ API request logs (GET /products, POST /auth/login, etc.)
- ✅ No ERROR logs (all requests should succeed)

### Frontend Console
Open browser DevTools (F12) → Console tab:

**Should see:**
- ✅ No red errors
- ✅ API calls to `http://localhost:8000/*`
- ✅ No CORS errors

## Step 8: Common Issues & Fixes

### Issue: Backend won't start
```
Error: bind: address already in use
```

**Fix**: Port 8000 is in use
```bash
# Kill process on port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
# Then kill the process
```

### Issue: Frontend can't reach API
```
CORS Error: blocked by CORS policy
```

**Fix**: Check backend is running
```bash
curl http://localhost:8000/health
```

### Issue: Database connection fails
```
Error: database connection refused
```

**Fix**: Wait for PostgreSQL to start (30 seconds)
```bash
docker logs ecommerce-db
```

### Issue: npm install hangs
```bash
# Clear cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

## Step 9: Cleanup

Stop all services:

```bash
# Stop frontend dev server
Ctrl+C  # in frontend terminal

# Stop backend
docker-compose down
```

## Checklist

### Backend ✅
- [ ] Health check returns `{"status": "ok"}`
- [ ] User registration works
- [ ] User login returns token
- [ ] Products list endpoint works
- [ ] Cart CRUD operations work
- [ ] Database has tables created
- [ ] No ERROR logs in backend

### Frontend ✅
- [ ] React app loads on http://localhost:3000
- [ ] Homepage displays
- [ ] Product listing page works
- [ ] Registration form submits
- [ ] Login works and stores token
- [ ] Shopping cart adds items
- [ ] Chat widget displays
- [ ] No CORS errors in console
- [ ] No JavaScript errors in console

### Integration ✅
- [ ] Frontend can fetch products from backend
- [ ] Frontend can register and login
- [ ] Cart operations sync between frontend and backend
- [ ] Logout clears tokens

## Next Steps

If everything passes:
1. ✅ Phase 3 (Local Testing) - **COMPLETE**
2. ⏳ Phase 4 - RAG Chatbot integration OR Azure deployment

## Support

For issues, check:
- Backend logs: `docker logs ecommerce-api`
- Frontend console: DevTools (F12)
- Database: `docker exec -it ecommerce-db psql ...`
- API docs: http://localhost:8000/docs (Swagger UI)
