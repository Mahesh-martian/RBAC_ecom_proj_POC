import React from "react";
import { ColumnDef } from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import { Category } from "@/redux/api/categoryApi";

export const AdminCategoryTableColumns: ColumnDef<Category>[] = [
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => <span>{row.original.name}</span>,
  },
  {
    accessorKey: "description",
    header: "Description",
    cell: ({ row }) => <span>{row.original.description}</span>,
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }) => (
      <div className="flex space-x-2">
        <Button
          onClick={() => console.log("Edit category:", row.original.id)}
          variant="outline"
        >
          Edit
        </Button>
        <Button
          onClick={() => console.log("Delete category:", row.original.id)}
          variant="destructive"
        >
          Delete
        </Button>
      </div>
    ),
  },
];
