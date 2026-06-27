"use client";

import { useSelector, useDispatch } from "react-redux";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { applyCoupon } from "@/redux/slices/cartSlice";
import { DataTable } from "@/components/shared/DataTable";
import { cartItemTableColumns } from "@/components/shared/tableColumnDef/CartItemTableColumn";
import { useRouter } from "next/navigation";
import { useToast } from "@/hooks/use-toast";

const Cart = () => {
  const dispatch = useDispatch();
  const router = useRouter();
  const { toast } = useToast();
  const { items, couponDiscount } = useSelector((state: any) => state.cart);
  const { user } = useSelector((state: any) => state.auth);
  const [couponCode, setCouponCode] = useState("");

  const subtotal = items.reduce(
    (sum: number, item: any) =>
      sum + (item.price - item.discount) * item.quantity,
    0,
  );
  const discountAmount = (subtotal * couponDiscount) / 100;
  const total = subtotal - discountAmount;

  const handleApplyCoupon = () => {
    // In a real app, you would validate the coupon code with your backend
    if (couponCode === "DISCOUNT20") {
      dispatch(applyCoupon({ code: couponCode, discount: 20 }));
    }
  };

  const handleCheckout = () => {
    if (!user) {
      toast({
        description: "You need to log in to proceed to checkout.",
        variant: "destructive",
      });
      router.push("/sign-in");
      return;
    }
    // Proceed to checkout logic here
    toast({
      description: "Proceeding to checkout...",
    });
    // For example, redirect to the checkout page
    router.push("/checkout");
  };

  return (
    <div className="container mx-auto py-10">
      <Card>
        <CardHeader>
          <CardTitle>Shopping Cart</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={cartItemTableColumns}
            data={items}
            pageIndex={0}
            totalPages={0}
            onPreviousPage={() => {}}
            onNextPage={() => {}}
          />

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="flex gap-2">
              <Input
                placeholder="Enter coupon code"
                value={couponCode}
                onChange={(e) => setCouponCode(e.target.value)}
              />
              <Button onClick={handleApplyCoupon}>Apply Coupon</Button>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span>₹{subtotal.toFixed(2)}</span>
              </div>
              {couponDiscount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Discount ({couponDiscount}%)</span>
                  <span>-₹{discountAmount.toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between font-bold">
                <span>Total</span>
                <span>₹{total.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button size="lg" onClick={handleCheckout}>
            Proceed to Checkout
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default Cart;
