import CustomBreadcrumb from "@/components/shared/CustomBreadcrumb";
import Heading from "@/components/shared/CustomHeading";
import { DataTable } from "@/components/shared/DataTable";
import { useGetAllFlashSalesQuery } from "@/redux/api/flashSaleApi";
import { ColumnDef } from "@tanstack/react-table";
import React, { useState } from "react";
import EditFlashSaleModal from "./Product/EditFlashSaleModal";
import CustomButton from "@/components/shared/CustomButton";
import { Pencil } from "lucide-react";

interface FlashSaleTableColumn {
  id: string;
  product: {
    name: string;
  };
  startTime: string;
  endTime: string;
  discount: number;
}

const VendorFlashSale = () => {
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [selectedFlashSale, setSelectedFlashSale] =
    useState<FlashSaleTableColumn | null>(null);

  const { data } = useGetAllFlashSalesQuery({
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

  const tableData: FlashSaleTableColumn[] =
    data?.data.map((flashSale: any) => ({
      id: flashSale.id,
      product: { name: flashSale.product.name },
      startTime: flashSale.startTime,
      endTime: flashSale.endTime,
      discount: flashSale.discount,
    })) || [];

  const flashSaleTableColumns: ColumnDef<FlashSaleTableColumn>[] = [
    { accessorKey: "product.name", header: "Product Name" },
    {
      accessorKey: "startTime",
      header: "Start Time",
      cell: ({ getValue }) => new Date(getValue<string>()).toLocaleString(),
    },
    {
      accessorKey: "endTime",
      header: "End Time",
      cell: ({ getValue }) => new Date(getValue<string>()).toLocaleString(),
    },
    {
      accessorKey: "discount",
      header: "Discount (%)",
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => {
        const flashSale = row.original;
        return (
          <CustomButton
            onClick={() => {
              setSelectedFlashSale(flashSale);
              setIsEditOpen(true);
            }}
            icon={<Pencil />}
          ></CustomButton>
        );
      },
    },
  ];

  return (
    <div>
      <CustomBreadcrumb
        items={[
          { label: "Home", path: "/" },
          { label: "Dashboard", path: "/dashboard/vendor" },
          { label: "Flash Sale" },
        ]}
        title="Flash Sale Page"
      />
      <div className="p-5">
        <div className="flex justify-center items-center pt-10 pb-10">
          <Heading text="Your Flash Sale" className="text-4xl lg:text-6xl" />
        </div>
        <DataTable
          data={tableData}
          columns={flashSaleTableColumns}
          pageIndex={page}
          totalPages={totalPages}
          onPreviousPage={handlePreviousPage}
          onNextPage={handleNextPage}
        />
      </div>
      {isEditOpen && selectedFlashSale && (
        <EditFlashSaleModal
          isOpen={isEditOpen}
          onClose={() => setIsEditOpen(false)}
          flashSale={selectedFlashSale}
        />
      )}
    </div>
  );
};

export default VendorFlashSale;
