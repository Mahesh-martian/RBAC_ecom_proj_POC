import { ColumnDef } from "@tanstack/react-table";
import Image from "next/image";
import { Minus, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDispatch } from "react-redux";
import { updateQuantity, removeFromCart } from "@/redux/slices/cartSlice";

interface CartItem {
  productId: string;
  name: string;
  price: number;
  quantity: number;
  image: string;
  discount: number;
}

// Component for rendering Quantity Actions
const QuantityActions = ({ item }: { item: CartItem }) => {
  const dispatch = useDispatch();

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="outline"
        size="icon"
        onClick={() =>
          dispatch(
            updateQuantity({
              productId: item.productId,
              quantity: item.quantity - 1,
            }),
          )
        }
        disabled={item.quantity <= 1}
      >
        <Minus className="h-4 w-4" />
      </Button>
      <span className="w-12 text-center">{item.quantity}</span>
      <Button
        variant="outline"
        size="icon"
        onClick={() =>
          dispatch(
            updateQuantity({
              productId: item.productId,
              quantity: item.quantity + 1,
            }),
          )
        }
      >
        <Plus className="h-4 w-4" />
      </Button>
    </div>
  );
};

// Component for rendering Delete Action
const DeleteAction = ({ productId }: { productId: string }) => {
  const dispatch = useDispatch();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => dispatch(removeFromCart(productId))}
      className="text-destructive hover:text-destructive"
    >
      <Trash2 className="h-4 w-4" />
    </Button>
  );
};

export const cartItemTableColumns: ColumnDef<CartItem>[] = [
  {
    header: "Product",
    cell: ({ row }) => {
      const item = row.original;
      return (
        <div className="flex items-center gap-4">
          <Image
            src={item.image[0]}
            alt={item.name}
            width={80}
            height={80}
            className="rounded-lg object-cover"
          />
          <span className="font-medium">{item.name}</span>
        </div>
      );
    },
  },
  {
    header: "Unit Price",
    cell: ({ row }) => {
      return <span>${row.original.price.toFixed(2)}</span>;
    },
  },
  {
    header: "Quantity",
    cell: ({ row }) => <QuantityActions item={row.original} />,
  },
  {
    header: "Total",
    cell: ({ row }) => {
      const total =
        (row.original.price - row.original.discount) * row.original.quantity;
      return <span className="font-medium">₹{total.toFixed(2)}</span>;
    },
  },
  {
    header: "Actions",
    cell: ({ row }) => <DeleteAction productId={row.original.productId} />,
  },
];
