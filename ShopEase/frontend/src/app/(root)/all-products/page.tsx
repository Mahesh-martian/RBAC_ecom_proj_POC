"use client";
import ProductFilters from "@/components/allProducts/ProductFilter";
import Heading from "@/components/shared/CustomHeading";
import ProductCard from "@/components/shared/ProductCard";
import SkeletonCard from "@/components/shared/SkeletonCard";
import { useGetProductsQuery } from "@/redux/api/productApi";
import { useSearchParams } from "next/navigation";
import React, { Suspense, useEffect, useRef, useState } from "react";

const AllProductContent = () => {
  const searchParams = useSearchParams();
  const queryParams: Record<string, any> = {};
  const [page, setPage] = useState(1);
  const [products, setProducts] = useState<any[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const observerRef = useRef<HTMLDivElement | null>(null);
  // Collect all query params
  searchParams.forEach((value, key) => {
    queryParams[key] = isNaN(Number(value)) ? value : Number(value); // Convert numbers
  });

  const { data, isLoading, isFetching } = useGetProductsQuery(
    { ...queryParams, page, limit: 10 },
    { skip: !hasMore },
  );
  useEffect(() => {
    if (data && data.length > 0) {
      setProducts((prev) => [...prev, ...data]);
      if (data.length < 10) {
        setHasMore(false); // No more products to load
      }
    }
  }, [data]);

  // Intersection Observer to load more products
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isFetching && hasMore) {
          setPage((prev) => prev + 1);
        }
      },
      { threshold: 1 },
    );

    if (observerRef.current) observer.observe(observerRef.current);

    return () => {
      if (observerRef.current) observer.unobserve(observerRef.current);
    };
  }, [isFetching, hasMore]);

  if (isLoading && page === 1) {
    return (
      <div className="flex flex-wrap justify-center gap-6 sm:grid-cols-1 lg:grid-cols-3 xl:grid-cols-4">
        {Array.from({ length: 10 }).map((_, idx) => (
          <SkeletonCard key={idx} />
        ))}
      </div>
    );
  }

  return (
    <div className="pb-20">
      <Heading
        text="Our Products"
        className="text-4xl lg:text-6xl text-center pb-20"
      />
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-y-8 md:gap-x-8 relative min-h-screen">
        <div className="col-span-1 sticky top-20 self-start">
          <ProductFilters />
        </div>
        <div className="col-span-1 md:col-span-2 lg:col-span-3">
          <div className="grid gap-6 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            {products.map((product) => (
              <ProductCard key={product.productId} product={product} />
            ))}
            {isFetching &&
              Array.from({ length: 3 }).map((_, idx) => (
                <SkeletonCard key={idx} />
              ))}
          </div>
          {!hasMore && (
            <p className="text-center mt-4">No more products to load.</p>
          )}
        </div>
      </div>
      <div ref={observerRef} className="h-10"></div> {/* Observer target */}
    </div>
  );
};

const AllProduct = () => (
  <Suspense
    fallback={
      <div className="flex justify-center items-center min-h-screen text-primary text-5xl font-semibold">
        Loading products...
      </div>
    }
  >
    <AllProductContent />
  </Suspense>
);

export default AllProduct;
