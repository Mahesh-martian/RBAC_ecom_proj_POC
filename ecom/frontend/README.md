# React E-Commerce Frontend

Modern React SPA for the FashionStore e-commerce platform with Stripe integration and RAG chatbot.

## Features

- ✅ Product browsing with advanced filtering and search
- ✅ Shopping cart with persistent storage
- ✅ User authentication (login/register)
- ✅ Checkout flow
- ✅ Order management and history
- ✅ RAG-powered chatbot widget
- ✅ Responsive design with Tailwind CSS
- ✅ Type-safe with TypeScript
- ✅ State management with Zustand
- ✅ Data fetching with TanStack Query

## Tech Stack

- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **API Client**: Axios
- **Data Fetching**: TanStack Query (React Query)
- **Routing**: React Router v6
- **Payments**: Stripe.js
- **Language**: TypeScript

## Project Structure

```
frontend/
├── src/
│   ├── pages/              # Page components
│   │   ├── Home.tsx
│   │   ├── ProductList.tsx
│   │   ├── ProductDetail.tsx
│   │   ├── Cart.tsx
│   │   ├── Checkout.tsx
│   │   ├── Orders.tsx
│   │   ├── OrderDetail.tsx
│   │   ├── Account.tsx
│   │   ├── NotFound.tsx
│   │   └── auth/
│   │       ├── Login.tsx
│   │       └── Register.tsx
│   ├── components/         # Reusable components
│   │   ├── layout/
│   │   │   ├── MainLayout.tsx
│   │   │   ├── AuthLayout.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Footer.tsx
│   │   └── ChatBot.tsx
│   ├── api/                # API client and endpoints
│   │   └── client.ts
│   ├── stores/             # Zustand stores
│   │   ├── authStore.ts
│   │   └── cartStore.ts
│   ├── types/              # TypeScript types
│   │   └── index.ts
│   ├── hooks/              # Custom hooks (placeholder)
│   ├── utils/              # Utility functions (placeholder)
│   ├── App.tsx             # Root component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── public/                 # Static assets
├── index.html              # HTML template
├── package.json            # Dependencies
├── vite.config.ts          # Vite configuration
├── tsconfig.json           # TypeScript configuration
├── tailwind.config.js      # Tailwind CSS configuration
├── postcss.config.js       # PostCSS configuration
└── README.md               # This file
```

## Getting Started

### Prerequisites

- Node.js 16+ and npm/yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Update the variables:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_STRIPE_PUBLIC_KEY=pk_test_your_key
```

### Development

```bash
npm run dev
```

Runs on `http://localhost:3000` with hot reload.

### Building

```bash
npm run build
```

Optimized production build in `dist/` directory.

### Type Checking

```bash
npm run type-check
```

Runs TypeScript compiler without emitting files.

### Linting

```bash
npm run lint
```

Checks code quality with ESLint.

## API Integration

The frontend communicates with the backend API at:

- **Development**: `http://localhost:8000`
- **Production**: Configure via `VITE_API_BASE_URL`

### Authentication Flow

1. User registers or logs in
2. Backend returns JWT tokens (access + refresh)
3. Access token stored in localStorage and Zustand store
4. All API requests include `Authorization: Bearer <token>` header
5. Invalid token triggers redirect to login

### State Management

**Auth Store** (`stores/authStore.ts`):
- User authentication
- Token management
- Profile data

**Cart Store** (`stores/cartStore.ts`):
- Cart items
- Cart operations (add, remove, update)
- Persisted to localStorage

## Pages

### Public Pages

- **Home** (`/`) - Featured products and categories
- **Product List** (`/products`) - Filterable product catalog
- **Product Detail** (`/products/:id`) - Single product with reviews
- **Login** (`/auth/login`) - User authentication
- **Register** (`/auth/register`) - New user registration

### Protected Pages

- **Cart** (`/cart`) - Shopping cart review
- **Checkout** (`/checkout`) - Order placement
- **Orders** (`/orders`) - Order history
- **Order Detail** (`/orders/:id`) - Single order tracking
- **Account** (`/account`) - User profile

## Components

### Layout Components

- **MainLayout**: Header, footer, main content area
- **AuthLayout**: Split screen with branding and form
- **Header**: Navigation, cart button, user menu
- **Footer**: Links and copyright

### Feature Components

- **ChatBot**: Floating widget with message interface
- **ProductCard**: Product display card
- **CategoryCard**: Category selection card

## Styling

Tailwind CSS with custom configuration:

- **Primary Color**: Purple (#5d2dff)
- **Secondary Color**: Orange (#fa3200)
- **Responsive Breakpoints**: sm, md, lg, xl, 2xl

### Utility Classes

- `.btn` - Base button styles
- `.btn-primary` - Primary action button
- `.btn-secondary` - Secondary button
- `.input` - Form input styling
- `.card` - Card container
- `.badge` - Tag/badge styling

## API Client

```typescript
// Example usage
import { productApi, authApi, cartApi } from '@api/client'

// Fetch products
const products = await productApi.list({ limit: 20, search: 'shirt' })

// Login
const auth = await authApi.login({ email, password })

// Add to cart
await cartApi.addItem(cartId, { product_id: 1, quantity: 2 })
```

## Error Handling

- API errors trigger user-friendly messages
- 401 Unauthorized redirects to login
- Validation errors displayed with field context
- Global error boundaries (coming soon)

## Performance Optimizations

- ✅ Code splitting via React Router
- ✅ Image lazy loading
- ✅ Query caching with TanStack Query
- ✅ Minified production builds
- ✅ Gzip compression ready

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari 14+, Chrome Android)

## Security

- ✅ JWT token-based authentication
- ✅ Secure HTTP-only headers
- ✅ CSRF protection via API
- ✅ Input sanitization
- ✅ XSS prevention

## Testing

(Coming Soon)

- Unit tests with Vitest
- Component tests with React Testing Library
- E2E tests with Playwright

## Deployment

### Vercel/Netlify

```bash
npm run build
# Deploy `dist/` folder
```

### Docker

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
RUN npm install -g serve
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

## Contributing

1. Create feature branch (`git checkout -b feature/amazing-feature`)
2. Commit changes (`git commit -m 'Add amazing feature'`)
3. Push to branch (`git push origin feature/amazing-feature`)
4. Open Pull Request

## Troubleshooting

### API Connection Issues

```bash
# Ensure backend is running
curl http://localhost:8000/health

# Check VITE_API_BASE_URL in .env
VITE_API_BASE_URL=http://localhost:8000
```

### Build Issues

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf .vite
npm run build
```

### Port Already in Use

```bash
# Change dev port in vite.config.ts
server: {
  port: 3001,  // Changed from 3000
}
```

## License

MIT

## Support

For issues and questions, contact: support@fashionstore.com
