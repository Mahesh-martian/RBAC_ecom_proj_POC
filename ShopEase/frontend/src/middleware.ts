import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import jwt, { Secret } from "jsonwebtoken";

interface DecodedToken {
  id: string;
  email: string;
  role: "ADMIN" | "VENDOR" | "CUSTOMER";
  name: string;
  vendor?: object | null;
  customer?: object | null;
}

const publicRoutes = ["/sign-in", "/sign-up", "/"];
const secretKey = process.env.NEXT_JWT_SECRET as Secret;

if (!secretKey) {
  throw new Error(
    "NEXT_JWT_SECRET is not defined in the environment variables",
  );
}

function decodeToken(token: string) {
  try {
    return jwt.verify(token, secretKey) as DecodedToken;
  } catch (error) {
    console.error("Error verifying token:", error);
    return null;
  }
}

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Allow public routes to bypass the middleware
  if (publicRoutes.some((route) => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  const token = req.cookies.get("accessToken")?.value;
  const user = token ? decodeToken(token) : null;

  if (!user || !user.role) {
    return NextResponse.redirect(new URL("/sign-in", req.url));
  }

  const protectedRoutes = {
    "/dashboard/admin": "ADMIN",
    "/dashboard/vendor": "VENDOR",
    "/dashboard/customer": "CUSTOMER",
  };

  // Check if the requested route is a protected route
  if (pathname in protectedRoutes) {
    const requiredRole =
      protectedRoutes[pathname as keyof typeof protectedRoutes];

    if (user.role !== requiredRole) {
      return NextResponse.redirect(new URL("/unauthorized", req.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
