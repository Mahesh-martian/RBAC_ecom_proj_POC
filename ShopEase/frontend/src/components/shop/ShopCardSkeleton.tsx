"use client";

import { Skeleton } from "@/components/ui/skeleton";

export function ShopCardSkeleton() {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex flex-row gap-4 items-center mb-4">
        <Skeleton className="w-16 h-16 rounded-full" />
        <div className="flex flex-col gap-2 flex-1">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      {/* Content */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <Skeleton className="h-12 w-full rounded-lg" />
        <Skeleton className="h-12 w-full rounded-lg" />
      </div>
      {/* Footer */}
      <Skeleton className="h-10 w-full rounded-lg" />
    </div>
  );
}
