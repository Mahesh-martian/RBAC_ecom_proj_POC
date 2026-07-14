"use client";

import { VendorProductActions } from "@/types";
import { ColumnDef } from "@tanstack/react-table";
import CustomButton from "../CustomButton";
import { Pencil, Copy, Tag } from "lucide-react";

export const vendorProductTableColumns: ColumnDef<VendorProductActions>[] = [
  { accessorKey: "categoryName", header: "Category Name" },
  { accessorKey: "name", header: "Name" },
  { accessorKey: "description", header: "Description" },
  { accessorKey: "price", header: "Price" },
  { accessorKey: "inventory", header: "Inventory" },
  { accessorKey: "discount", header: "Discount" },
  {
    accessorKey: "actions",
    header: "Actions",
    cell: ({ row }) => {
      const product: VendorProductActions = row.original;

      return (
        <div className="flex space-x-2">
          <CustomButton
            className=""
            icon={<Pencil />}
            onClick={() => product.handleEdit(product)}
          ></CustomButton>
          <CustomButton
            className=""
            icon={<Copy />}
            onClick={() => product.handleDuplicate(product)}
          ></CustomButton>
          <CustomButton
            icon={<Tag />}
            onClick={() => product.handleFlashSale(product)}
          />
        </div>
      );
    },
  },
];
