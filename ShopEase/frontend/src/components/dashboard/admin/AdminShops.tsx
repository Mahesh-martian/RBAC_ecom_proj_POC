import CustomBreadcrumb from "@/components/shared/CustomBreadcrumb";
import Heading from "@/components/shared/CustomHeading";
import { DataTable } from "@/components/shared/DataTable";
import { Button } from "@/components/ui/button";
import { useBlacklistVendorMutation } from "@/redux/api/adminApi";
import { useGetAllShopQuery } from "@/redux/api/shopApi";
import { ShopRouteShopData } from "@/types";
import { ColumnDef } from "@tanstack/react-table";
import React, { useState } from "react";

const AdminShops = () => {
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const { data, isLoading } = useGetAllShopQuery({ page: 1, limit: 10 });
  const [blacklistVendor, { isLoading: isBlacklisting }] =
    useBlacklistVendorMutation();

  const totalPages = Math.ceil((data?.meta?.total || 0) / limit);

  const handlePreviousPage = () => {
    if (page > 1) setPage((prev) => prev - 1);
  };

  const handleNextPage = () => {
    if (page < totalPages) setPage((prev) => prev + 1);
  };

  const columns: ColumnDef<ShopRouteShopData>[] = [
    {
      accessorKey: "name",
      header: "Shop Name",
      cell: (info) => info.getValue(),
    },
    {
      accessorKey: "description",
      header: "Description",
      cell: (info) => info.getValue(),
    },
    {
      accessorKey: "followers",
      header: "Followers",
      cell: (info) => info.getValue(),
    },
    {
      accessorKey: "productsQuantity",
      header: "Products Quantity",
      cell: (info) => info.getValue(),
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => {
        const shopId = row.original.shopId;
        const isBlackListed = row.original.isBlackListed;
        return (
          <Button
            onClick={() => handleBlacklist(shopId, !isBlackListed)}
            disabled={isBlacklisting}
            className={`${
              isBlackListed ? "bg-green-500" : "bg-red-500"
            } text-white`}
          >
            {isBlackListed ? "Remove Blacklist" : "Blacklist"}
          </Button>
        );
      },
    },
  ];

  const handleBlacklist = async (shopId: string, isBlackListed: boolean) => {
    try {
      await blacklistVendor({ shopId, isBlackListed }).unwrap();
      console.log(
        `${isBlackListed ? "BlackListed" : "Removed from BlackListed"} vendor ${shopId}`,
      );
    } catch (error) {
      console.error("Error isBlackListed vendor:", error);
    }
  };

  return (
    <div>
      <CustomBreadcrumb
        items={[
          { label: "Home", path: "/" },
          { label: "Dashboard", path: "/dashboard/admin" },
          { label: "Shops" },
        ]}
        title="Shops Page"
      />
      <div className="p-5">
        <div className="flex justify-center items-center pt-10 pb-10">
          <Heading text="Shops" className="text-4xl lg:text-6xl" />
        </div>
        <DataTable
          data={data?.data || []}
          columns={columns}
          pageIndex={page}
          totalPages={totalPages}
          onPreviousPage={handlePreviousPage}
          onNextPage={handleNextPage}
        />
      </div>
    </div>
  );
};

export default AdminShops;
