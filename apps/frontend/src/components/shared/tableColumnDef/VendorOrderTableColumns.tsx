import { Order } from "@/types";
import { ColumnDef } from "@tanstack/react-table";

export const orderTableColumns: ColumnDef<Order>[] = [
  {
    accessorKey: "createdAt",
    header: "Order Date",
    cell: ({ getValue }) => new Date(getValue<string>()).toLocaleDateString(),
  },
  {
    accessorKey: "totalAmount",
    header: "Amount",
    cell: ({ getValue }) => `$${getValue<number>()}`,
  },
  {
    accessorKey: "status",
    header: "Status",
  },
  {
    accessorKey: "itemsCount",
    header: "Number of Items",
  },
];
