"use client";

import { useEffect, useState } from "react";
import { Star } from "lucide-react";
import { useParams } from "next/navigation";
import {
  useGetProductsQuery,
  useGetSingleProductQuery,
} from "@/redux/api/productApi";
import ProductImages from "@/components/product/ProductImages";
import ProductInfo from "@/components/product/ProductInfo";
import ReviewSection from "@/components/product/ReviewSection";
import { useDispatch } from "react-redux";
import { addProductId } from "@/redux/slices/recentProductsSlice";
import ProductCard from "@/components/shared/ProductCard";
import SkeletonCard from "@/components/shared/SkeletonCard";
import Heading from "@/components/shared/CustomHeading";
import ProductDetailsSkeleton from "@/components/product/ProductDetailsSkeleton";

export default function ProductDetails() {
  const { id } = useParams();
  const { data: product, isLoading: isSingleProductLoading } =
    useGetSingleProductQuery({
      id: id as string,
    });
  const dispatch = useDispatch();
  const [quantity, setQuantity] = useState(1);

  useEffect(() => {
    if (product?.productId) {
      dispatch(addProductId(product.productId));
    }
  }, [product, dispatch]);

  const { data: relatedProducts, isLoading: isRelatedProductsLoading } =
    useGetProductsQuery({
      categoryId: product?.categoryId,
    });

  if (isSingleProductLoading) {
    return <ProductDetailsSkeleton />;
  }
  if (!product) return <div>Product not found</div>;

  const renderStars = (rating: number) => {
    return Array(5)
      .fill(0)
      .map((_, i) => (
        <Star
          key={i}
          className={`w-5 h-5 ${i < rating ? "fill-primary text-primary" : "fill-muted text-muted-foreground"}`}
        />
      ));
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid md:grid-cols-2 gap-8">
        {/* Product Images */}
        <ProductImages product={product} />

        {/* Product Info */}
        <ProductInfo
          product={product}
          quantity={quantity}
          setQuantity={setQuantity}
          renderStars={renderStars}
        />
      </div>

      {/* Reviews Section */}
      <ReviewSection product={product} renderStars={renderStars} />
      <div className="py-20">
        <Heading
          text="Related Products"
          className="text-4xl lg:text-6xl text-center pb-20"
        />
        <div className="flex flex-wrap justify-center gap-6 sm:grid-cols-1 lg:grid-cols-3 xl:grid-cols-4">
          {relatedProducts
            ?.slice(0, 3)
            .map((product) => (
              <ProductCard key={product.productId} product={product} />
            ))}
          {isRelatedProductsLoading &&
            Array.from({ length: 3 }).map((_, idx) => (
              <SkeletonCard key={idx} />
            ))}
        </div>
      </div>
    </div>
  );
}
