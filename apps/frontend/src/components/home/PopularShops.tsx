"use client";
import Heading from "@/components/shared/CustomHeading";
import { ShopCard } from "@/components/shop/ShopCard";
import { ShopCardSkeleton } from "@/components/shop/ShopCardSkeleton";
import { useGetAllShopQuery } from "@/redux/api/shopApi";
import Link from "next/link";

const PopularShops = () => {
  const { data, isLoading } = useGetAllShopQuery({ page: 1, limit: 3 });

  return (
    <>
      <div className="pt-20">
        <Heading
          text="Popular Shops"
          className="text-4xl lg:text-6xl text-center pb-20"
        />
      </div>

      <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 pb-20">
        {isLoading
          ? Array.from({ length: 6 }).map((_, index) => (
              <ShopCardSkeleton key={index} />
            ))
          : data &&
            data?.data.map((shop) => (
              <ShopCard key={shop.shopId} shop={shop} />
            ))}
      </div>

      <div className="flex justify-center items-center mt-6">
        <Link
          href="/shop"
          className="bg-black text-white py-3 px-8 font-medium rounded-md bg-opacity-90 hover:bg-opacity-100 duration-300"
        >
          View All
        </Link>
      </div>
    </>
  );
};

export default PopularShops;
