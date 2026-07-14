"use client";
import HomeCarousel from "@/components/home/Carousel";
import Category from "@/components/home/Category";
import HomeFlashSale from "@/components/home/HomeFlashSale";
import PopularShops from "@/components/home/PopularShops";
import Products from "@/components/home/Products";
import WhyChooseUs from "@/components/home/WhyChooseUs";

export default function Home() {
  return (
    <div className="px-5 pb-20">
      <HomeCarousel />
      <Category />
      <Products />
      <WhyChooseUs />
      <HomeFlashSale />
      <PopularShops />
    </div>
  );
}
