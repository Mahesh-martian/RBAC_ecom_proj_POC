import React from "react";
import { ColumnDef } from "@tanstack/react-table";

export const AdminTransactionTableColumns: ColumnDef<any>[] = [
  {
    accessorKey: "customerId",
    header: "Customer ID",
    cell: ({ row }) => <span>{row.original.customerId}</span>,
  },
  {
    accessorKey: "orderId",
    header: "Order ID",
    cell: ({ row }) => <span>{row.original.orderId}</span>,
  },
  {
    accessorKey: "paymentMethod",
    header: "Payment Method",
    cell: ({ row }) => <span>{row.original.paymentMethod}</span>,
  },
  {
    accessorKey: "amount",
    header: "Amount",
    cell: ({ row }) => <span>{row.original.amount}</span>,
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <span>{row.original.status}</span>,
  },
];
