import CustomBreadcrumb from "@/components/shared/CustomBreadcrumb";
import Heading from "@/components/shared/CustomHeading";
import { DataTable } from "@/components/shared/DataTable";
import { orderTableColumns } from "@/components/shared/tableColumnDef/VendorOrderTableColumns";
import { useGetAllOrdersQuery } from "@/redux/api/orderApi";
import { Order } from "@/types";
import React, { useState } from "react";

const VendorOrders = () => {
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const { data } = useGetAllOrdersQuery({
    page,
    limit,
  });

  // Transform the API response to match the table structure
  const tableData: Order[] =
    data?.data.map((order: Order) => ({
      ...order,
      itemsCount: order?.order_items?.length as number,
    })) || [];

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
          { label: "Dashboard", path: "/dashboard/vendor" },
          { label: "Order" },
        ]}
        title="Order Page"
      />
      <div className="p-5">
        <div className="flex justify-center items-center pt-10 pb-10">
          <Heading
            text="Your Customer Orders"
            className="text-4xl lg:text-6xl"
          />
        </div>
        <DataTable
          data={tableData}
          columns={orderTableColumns}
          pageIndex={page}
          totalPages={totalPages}
          onPreviousPage={handlePreviousPage}
          onNextPage={handleNextPage}
        />
      </div>
    </div>
  );
};

export default VendorOrders;
