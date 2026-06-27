"use client";

import React from "react";
import { Skeleton } from "@/components/ui/skeleton";

const ProductDetailsSkeleton = () => {
  return (
    <div className="space-y-10">
      {/* Skeleton for Product Images */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-4">
          <Skeleton className="w-full aspect-square rounded-lg" />
          <div className="flex gap-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="w-24 aspect-square rounded-md" />
            ))}
          </div>
        </div>

        {/* Skeleton for Product Info */}
        <div className="space-y-6">
          <Skeleton className="h-6 w-1/4" />
          <Skeleton className="h-10 w-1/2" />
          <Skeleton className="h-6 w-1/3" />
          <Skeleton className="h-12 w-1/4" />

          <div className="space-y-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>

          <div className="space-y-2">
            <Skeleton className="h-6 w-1/4" />
            <div className="flex gap-2">
              {Array.from({ length: 5 }).map((_, index) => (
                <Skeleton key={index} className="w-6 h-6 rounded-full" />
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Skeleton className="h-6 w-1/4" />
            <Skeleton className="h-10 w-24" />
          </div>

          <div className="flex gap-4">
            <Skeleton className="h-10 w-1/3" />
            <Skeleton className="h-10 w-1/3" />
          </div>
        </div>
      </div>

      {/* Skeleton for Features */}
      <div className="grid grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} className="h-16 w-full rounded-lg" />
        ))}
      </div>

      {/* Skeleton for Reviews Section */}
      <div className="space-y-6">
        <Skeleton className="h-6 w-1/4" />
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="space-y-4 border-b pb-6">
            <div className="flex gap-4 items-center">
              <Skeleton className="h-6 w-1/4" />
              <Skeleton className="h-4 w-1/6" />
            </div>
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-4 w-full" />
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProductDetailsSkeleton;
