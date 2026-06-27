"use client";
import CustomBreadcrumb from "@/components/shared/CustomBreadcrumb";
import Heading from "@/components/shared/CustomHeading";
import { useGetAdminUsersQuery } from "@/redux/api/adminApi";
import React, { useState } from "react";

const AdminProducts = () => {
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const { data } = useGetAdminUsersQuery({ page, limit });

  const totalPages = Math.ceil((data?.meta?.total || 0) / limit);

  const handlePreviousPage = () => {
    if (page > 1) setPage((prev) => prev - 1);
  };

  const handleNextPage = () => {
    if (page < totalPages) setPage((prev) => prev + 1);
  };

  return (
    <div>
      <CustomBreadcrumb
        items={[
          { label: "Home", path: "/" },
          { label: "Dashboard", path: "/dashboard/admin" },
          { label: "Products" },
        ]}
        title="Products Page"
      />
      <div className="p-5">
        <div className="flex justify-center items-center pt-10 pb-10">
          <Heading text="Products" className="text-4xl lg:text-6xl" />
        </div>
        {/* <DataTable
          data={}
          columns={}
          pageIndex={page}
          totalPages={totalPages}
          onPreviousPage={handlePreviousPage}
          onNextPage={handleNextPage}
        /> */}
      </div>
    </div>
  );
};

export default AdminProducts;
