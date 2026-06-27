import { ColumnDef } from "@tanstack/react-table";

export interface CustomerOrderTableData {
  date: string;
  amount: number;
  quantity: number;
  status: string;
}

export const CustomerOrderTableColumns: ColumnDef<CustomerOrderTableData>[] = [
  {
    accessorKey: "date",
    header: "Date",
    cell: (info) => info.getValue(),
  },
  {
    accessorKey: "amount",
    header: "Amount",
    cell: (info) => `$${info.getValue()}`,
  },
  {
    accessorKey: "quantity",
    header: "Quantity",
    cell: (info) => info.getValue(),
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: (info) => info.getValue(),
  },
];
