"use client";
import CustomBreadcrumb from "@/components/shared/CustomBreadcrumb";
import Heading from "@/components/shared/CustomHeading";
import { DataTable } from "@/components/shared/DataTable";
import { CustomerOrderTableColumns } from "@/components/shared/tableColumnDef/CustomerOrderTableColumns";
import { useGetAllOrdersQuery } from "@/redux/api/orderApi";
import { Order } from "@/types";
import React, { useState } from "react";

const CustomerOrders = () => {
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const { data } = useGetAllOrdersQuery({
    page,
    limit,
  });

  const totalPages = Math.ceil((data?.meta?.total || 0) / limit);

  const handlePreviousPage = () => {
    if (page > 1) setPage((prev) => prev - 1);
  };

  const handleNextPage = () => {
    if (page < totalPages) setPage((prev) => prev + 1);
  };

  // Organize data into the Order interface structure
  const orders: Order[] =
    data?.data?.map((order: any) => ({
      id: order.id,
      customerId: order.customerId,
      vendorId: order.vendorId,
      totalAmount: order.totalAmount,
      status: order.status,
      createdAt: order.createdAt,
      updatedAt: order.updatedAt,
      deletedAt: order.deletedAt,
      order_items: order.order_items?.map((item: any) => ({
        id: item.id,
        orderId: item.orderId,
        productId: item.productId,
        quantity: item.quantity,
        price: item.price,
        discount: item.discount,
        createdAt: item.createdAt,
        updatedAt: item.updatedAt,
      })),
    })) || [];

  const customerOrderTableData =
    orders?.map((order: Order) => ({
      date: new Date(order.createdAt).toLocaleDateString(),
      amount: order.totalAmount,
      quantity: order.order_items?.length || 0,
      status: order.status,
    })) || [];

  return (
    <div>
      <CustomBreadcrumb
        items={[
          { label: "Home", path: "/" },
          { label: "Dashboard", path: "/dashboard/customer" },
          { label: "Order" },
        ]}
        title="Order Page"
      />
      <div className="p-5">
        <div className="flex justify-center items-center pt-10 pb-10">
          <Heading text="Your Orders" className="text-4xl lg:text-6xl" />
        </div>
        <DataTable
          data={customerOrderTableData}
          columns={CustomerOrderTableColumns}
          pageIndex={page}
          totalPages={totalPages}
          onPreviousPage={handlePreviousPage}
          onNextPage={handleNextPage}
        />
      </div>
    </div>
  );
};

export default CustomerOrders;
