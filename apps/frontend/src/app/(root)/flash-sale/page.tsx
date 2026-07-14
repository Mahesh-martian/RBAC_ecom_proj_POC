"use client";
import Heading from "@/components/shared/CustomHeading";
import ProductCard from "@/components/shared/ProductCard";
import SkeletonCard from "@/components/shared/SkeletonCard";
import { useGetAllFlashSalesQuery } from "@/redux/api/flashSaleApi";
import { ProductData } from "@/types";
import React, { useState } from "react";

const FlashSale = () => {
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const { data, isLoading } = useGetAllFlashSalesQuery({
    page,
    limit,
  });

  const transformedData: ProductData[] =
    data?.data?.map((item) => {
      const product = item.product;
      return {
        productId: product.id,
        name: product.name,
        description: product.description,
        categoryId: product.categoryId || "unknown",
        discount: item.discount,
        image: product.image || [],
        inventory: product.inventory || 0,
        price: product.price,
        shopId: product.shopId || "unknown",
        vendorId: product.vendorId || "unknown",
      };
    }) || [];

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
    <div>
      <Heading
        text="Flash Sale Products"
        className="text-4xl lg:text-6xl text-center py-20"
      />

      <div className="flex flex-wrap justify-center gap-6 sm:grid-cols-1 lg:grid-cols-3 xl:grid-cols-4">
        {transformedData?.map((product) => (
          <ProductCard key={product.productId} product={product} />
        ))}
      </div>
    </div>
  );
};

export default FlashSale;
