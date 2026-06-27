"use client";

import React, { useEffect } from "react";
import { useSelector } from "react-redux";
import { RootState } from "@/redux/store";
import { usePathname, useRouter } from "next/navigation";

interface ProtectedRouteProps {
  allowedRoles: { [key: string]: string[] }; // Define allowed roles for each slug
  children: React.ReactNode;
}

const ProtectedRoute = ({ allowedRoles, children }: ProtectedRouteProps) => {
  const user = useSelector((state: RootState) => state.auth.user);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!user) {
      // Redirect to login if not authenticated
      router.push("/sign-in");
      return;
    }

    // Extract the slug dynamically
    const slug = pathname.split("/dashboard/")[1];

    // Check if the slug has allowed roles
    const rolesForSlug = allowedRoles[slug];
    if (!rolesForSlug || !rolesForSlug.includes(user.role)) {
      // Redirect to unauthorized if the user doesn't have access
      router.push("/unauthorized");
    }
  }, [user, allowedRoles, router, pathname]);

  // Show nothing while validating
  if (!user) {
    return null;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
