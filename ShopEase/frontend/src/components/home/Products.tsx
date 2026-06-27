import ProductCard from "../shared/ProductCard";
import { useGetProductsQuery } from "@/redux/api/productApi";
import Heading from "../shared/CustomHeading";
import { ProductData } from "@/types";
import SkeletonCard from "../shared/SkeletonCard";
import Link from "next/link";

const Products = () => {
  const { data, isLoading, isFetching } = useGetProductsQuery({
    page: 1,
    limit: 4,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center gap-4 flex-wrap">
        {Array.from({ length: 4 }).map((_, idx) => (
          <SkeletonCard key={idx} />
        ))}
      </div>
    );
  }

  return (
    <div>
      <Heading
        text="Our Products"
        className="text-4xl lg:text-6xl text-center pb-20"
      />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 md:grid-cols-3 xl:grid-cols-4">
        {data?.map((product: ProductData) => (
          <ProductCard key={product.productId} product={product} />
        ))}
        {isFetching &&
          Array.from({ length: 4 }).map((_, idx) => <SkeletonCard key={idx} />)}
      </div>

      <div className="flex justify-center items-center mt-6">
        <Link
          href="/all-products"
          className="bg-black text-white py-3 px-8 font-medium rounded-md bg-opacity-90 hover:bg-opacity-100 duration-300"
        >
          View All
        </Link>
      </div>
    </div>
  );
};

export default Products;
