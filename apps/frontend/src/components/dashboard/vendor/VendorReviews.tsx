import React, { useState } from "react";
import CustomBreadcrumb from "@/components/shared/CustomBreadcrumb";
import { Review, useGetReviewsQuery } from "@/redux/api/reviewApi";
import { DataTable } from "@/components/shared/DataTable";
import { reviewTableColumns } from "@/components/shared/tableColumnDef/VendorReviewTableColumn";

const VendorReviews = () => {
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const { data, error, isLoading } = useGetReviewsQuery({ page, limit });

  const totalPages = Math.ceil((data?.meta?.total || 0) / limit);

  const handlePreviousPage = () => {
    if (page > 1) setPage((prev) => prev - 1);
  };

  const handleNextPage = () => {
    if (page < totalPages) setPage((prev) => prev + 1);
  };

  if (isLoading) {
    return <p>Loading...</p>;
  }

  if (error) {
    return <p>Error loading reviews!</p>;
  }

  // Transform API data into a format compatible with the DataTable
  const tableData: Review[] =
    data?.data.map((review: Review) => ({
      id: review.id,
      comment: review.comment,
      rating: review.rating,
      customer: {
        id: review.customer.id,
        name: review.customer.name,
        email: review.customer.email,
        createdAt: review.customer.createdAt,
        updatedAt: review.customer.updatedAt,
        isDeleted: review.customer.isDeleted,
        isSuspended: review.customer.isSuspended,
        profilePhoto: review.customer.profilePhoto,
      },
      product: {
        id: review.product.id,
        name: review.product.name,
        description: review.product.description,
        categoryId: review.product.categoryId,
        price: review.product.price,
        discount: review.product.discount,
        inventory: review.product.inventory,
        shopId: review.product.shopId,
        vendorId: review.product.vendorId,
        createdAt: review.product.createdAt,
        updatedAt: review.product.updatedAt,
        deletedAt: review.product.deletedAt,
        image: review.product.image,
      },
      createdAt: review.createdAt,
      updatedAt: review.updatedAt,
    })) || [];

  return (
    <div>
      <CustomBreadcrumb
        items={[
          { label: "Home", path: "/" },
          { label: "Dashboard", path: "/dashboard/vendor" },
          { label: "Review" },
        ]}
        title="Review Page"
      />
      <div className="p-5">
        <h2 className="text-2xl font-bold mb-5">Vendor Reviews</h2>
        <DataTable
          data={tableData}
          columns={reviewTableColumns}
          pageIndex={page}
          totalPages={totalPages}
          onNextPage={handleNextPage}
          onPreviousPage={handlePreviousPage}
        />
      </div>
    </div>
  );
};

export default VendorReviews;
