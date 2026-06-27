import { Review } from "@/redux/api/reviewApi";
import { ColumnDef } from "@tanstack/react-table";

export const reviewTableColumns: ColumnDef<Review>[] = [
  {
    accessorKey: "comment",
    header: "Comment",
  },
  {
    accessorKey: "rating",
    header: "Rating",
    cell: ({ getValue }) => `${getValue<number>()} ★`, // Add star symbol
  },
  {
    accessorKey: "customer.name",
    header: "Customer Name",
  },
  {
    accessorKey: "product.name",
    header: "Product Name",
  },
];
