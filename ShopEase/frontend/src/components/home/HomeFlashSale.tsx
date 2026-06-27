"use client";
import Heading from "@/components/shared/CustomHeading";
import ProductCard from "@/components/shared/ProductCard";
import { useGetAllFlashSalesQuery } from "@/redux/api/flashSaleApi";
import { ProductData } from "@/types";
import Link from "next/link";

const HomeFlashSale = () => {
  const { data } = useGetAllFlashSalesQuery({
    page: 1,
    limit: 4,
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

  return (
    <div>
      <Heading
        text="Flash Sale Products"
        className="text-4xl lg:text-6xl text-center py-20"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 md:grid-cols-3 xl:grid-cols-4">
        {transformedData?.map((product) => (
          <ProductCard key={product.productId} product={product} />
        ))}
      </div>

      <div className="flex justify-center items-center mt-6">
        <Link
          href="/flash-sale"
          className="bg-black text-white py-3 px-8 font-medium rounded-md bg-opacity-90 hover:bg-opacity-100 duration-300"
        >
          View More
        </Link>
      </div>
    </div>
  );
};

export default HomeFlashSale;
