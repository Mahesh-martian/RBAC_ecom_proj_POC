# Shop Ease

## Introduction

Shop Ease is a modern e-commerce platform designed to provide a seamless online shopping experience for users, vendors, and administrators. This responsive and scalable application is built using cutting-edge web development technologies to ensure a robust, secure, and high-performance system.

## Project Description

Shop Ease serves as a comprehensive platform for online shopping. Users can browse and purchase products, vendors can manage their shops and inventories, and administrators can monitor and moderate activities across the system. The project is designed to provide an intuitive interface for all user roles, focusing on scalability, responsiveness, and security.

### Key objectives:

Enable a seamless shopping experience for customers with advanced filtering and comparison features.
Empower vendors with tools to manage their shops effectively.
Provide administrators with control over platform-wide operations, ensuring smooth and secure transactions.

## Technologies include:

- Frontend: Next.js with Tailwind CSS and shadcn ui for a modern, responsive UI.
- Backend: Node.js with Express.js for a robust API.
- Database: PostgreSQL for secure and efficient data storage.
- Payment Integration: Stripe.
- Cloud Storage: Cloudinary for image uploads.

## Features

### Admin

- Manage users (suspend/delete accounts).
- Control product categories dynamically (add/edit/delete).
- Monitor platform activities, transactions, and vendor performance.
- Blacklist vendors or shops.

### Vendor

- Manage shop details and inventory (add/edit/delete products).
- View and respond to customer reviews.
- Paginated order and product lists for better management.

### Customer

- Browse and filter products by category, price, and keywords.
- Add items to the cart and manage checkout seamlessly.
- Apply coupon codes for discounts during checkout.
- View order history and recently viewed products.
- Follow vendor shops for updates on their products.

### Additional Features

- JWT-based secure authentication with password reset functionality.
- Responsive design optimized for mobile and desktop.
- Infinite scrolling on the homepage.
- Product details page with related products and customer reviews.
- Dark and light mode. 

## Technology Stack

### Frontend
- Next.js
- Tailwind CSS
- React Hook Form
- Shadcn Ui
- Redux
- RTK Quary
- Typescript
- Zod 

### Backend
- Node.js
- Express.js
- Prisma ORM
- Cloudinary (image hosting)
- Nodemailer (email notifications)
- Typescript
- Zod

### Database
- PostgreSQL

### Payment Integration
Stripe

## Installation Guidelines

### Prerequisites
- Node.js installed on your system.
- PostgreSQL database set up.
- Cloudinary account for image storage.
- Stripe account for payment integration.

### Steps

1. Clone the repository:

```bash
git clone https://github.com/enayetsyl/ShopEase.git
```

2. Navigate to the project folder:

```bash 
cd ShopEase
```

3. Set up the backend:

```bash 
cd backend
npm install
```

4. Configure the .env file for the backend with the following:

```bash 
NODE_ENV="development"
PORT=5002
DATABASE_URL=
JWT_SECRET=
JWT_EXPIRES_IN="30d"
JWT_REFRESH_TOKEN_SECRET=
JWT_REFRESH_TOKEN_EXPIRES_IN="30d"
JWT_RESET_PASS_TOKEN=
JWT_RESET_PASS_TOKEN_EXPIRES_IN="5m"
RESET_PASS_LINK=http://localhost:3000/reset-password
NODEMAILER_EMAIL=
NODEMAILER_APP_PASS=
CLOUDINARY_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_SECRET=
NEXT_PAYMENT_GATEWAY_PUBLIC_KEY=
STRIPE_SECRET_KEY=
ADMIN_EMAIL=
ADMIN_PASSWORD=
```

5. Start the backend server:

```bash 
npm run dev
```

6. Set up the frontend

```bash 
cd ../frontend
npm install
```

7. Configure the .env file for the frontend with the following

```bash 
NEXT_JWT_SECRET=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
NEXT_BACKEND_BASE_URL=http://localhost:5002/api/v1
```

8. Start the frontend server:

```bash 
npm run dev
```


## Usage

- Customer: Browse products, add items to the cart, and complete checkout using Stripe.
- Vendor: Manage your shop, upload products, and view order history.
- Admin: Oversee all activities and manage user/vendor/shop operations.

## Live Links

- Shop Ease Frontend ([Live](https://shop-ease-8a83-fe.vercel.app/)) 
- GitHub Repository ([Link](https://github.com/enayetsyl/ShopEase.git))

## Statistics
- Lines of code pushed in github.
  
![Homepage Screenshot](https://res.cloudinary.com/deqyxkw0y/image/upload/v1734187146/git-hub-code_contribution_lqvsmx.png)

### Contact Information

- [Email](enayetflweb@gmail.com)
- [Linkedin](https://www.linkedin.com/in/md-enayetur-rahman/)
- [github](https://github.com/enayetsyl)
- [facebook](https://www.facebook.com/profile.php?id=100094416483981)
- [X](https://x.com/enayetu_syl)


## Conclusion

Shop Ease is a scalable and feature-rich e-commerce solution designed to meet the needs of diverse stakeholders. It leverages modern technologies to ensure a seamless experience, making it a standout platform for online shopping.












