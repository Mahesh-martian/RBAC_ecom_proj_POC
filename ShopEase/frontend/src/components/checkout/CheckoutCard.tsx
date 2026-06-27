"use client";

import { CardElement, useElements, useStripe } from "@stripe/react-stripe-js";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "@/redux/store";
import {
  useCreatePaymentIntentMutation,
  useSavePaymentMutation,
} from "@/redux/api/paymentApi";
import { useCreateOrderMutation } from "@/redux/api/orderApi";
import { useToast } from "@/hooks/use-toast";
import PaymentForm from "../forms/PaymentForm";
import { useRouter } from "next/navigation";
import { clearCart } from "@/redux/slices/cartSlice";

export default function CheckoutCard() {
  const stripe = useStripe();
  const elements = useElements();
  const [createPaymentIntent] = useCreatePaymentIntentMutation();
  const [savePayment] = useSavePaymentMutation();
  const { toast } = useToast();
  const dispatch = useDispatch();
  const router = useRouter();
  const [clientSecret, setClientSecret] = useState<string>("");
  const [transactionId, setTransactionId] = useState<string>("");
  const [metaData, setMetaData] = useState({});
  const [createOrder] = useCreateOrderMutation();
  const [error, setError] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  // Access cart data from Redux store
  const { items, couponDiscount } = useSelector(
    (state: RootState) => state.cart,
  );

  // Calculate totals
  const subtotal = items.reduce(
    (sum, item) => sum + (item.price - item.discount) * item.quantity,
    0,
  );
  const discountAmount = (subtotal * couponDiscount) / 100;
  const shippingCost = 10.0;
  const total = subtotal - discountAmount + shippingCost;

  // Prepare structured data

  // Log structured cart data

  useEffect(() => {
    const fetchClientSecret = async () => {
      try {
        const response = await createPaymentIntent({ amount: total }).unwrap();
        setClientSecret(response.data.client_secret);

        setMetaData(response.data);
      } catch (err) {
        console.error("Error creating payment intent:", err);
        setError("Failed to initialize payment. Please try again.");
      }
    };

    fetchClientSecret();
  }, [createPaymentIntent, total]);

  const handleOrderSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setIsLoading(true);

    const card = elements.getElement(CardElement);

    if (card === null) {
      return;
    }

    const { error } = await stripe.createPaymentMethod({
      type: "card",
      card,
    });

    if (error) {
      setError(error.message ?? "An error occurred");
    } else {
      setError("");
    }

    try {
      const { paymentIntent, error: confirmError } =
        await stripe.confirmCardPayment(clientSecret, {
          payment_method: {
            card: card,
          },
        });
      setMetaData(paymentIntent || {});
      if (confirmError) {
        toast({
          description: confirmError?.message || "Payment failed",
          variant: "destructive",
        });
      } else {
        if (paymentIntent.status === "succeeded") {
          setTransactionId(paymentIntent.id);
          toast({
            description: "Payment successful!",
          });

          const structuredCartData = {
            vendorId: items[0].vendorId,
            totalAmount: Number(total.toFixed(2)),
            products: items.map((item) => ({
              productId: item.productId,
              quantity: item.quantity,
              price: item.price,
              discount: item.discount,
            })),
          };

          try {
            const createOrderResponse =
              await createOrder(structuredCartData).unwrap();
            if (createOrderResponse.success) {
              const savePaymentData = {
                orderId: createOrderResponse.data.id,
                customerId: createOrderResponse.data.customerId,
                amount: createOrderResponse.data.totalAmount,
                transactionId: paymentIntent.id,
                status: "SUCCESS",
                metadata: metaData,
              };

              const savePaymentResponse =
                await savePayment(savePaymentData).unwrap();

              if (savePaymentResponse.success) {
                toast({
                  description: savePaymentResponse.message,
                });

                // Clear the cart
                dispatch(clearCart());

                // Redirect to home page
                router.push("/");
              }
            }
          } catch (err) {
            console.error("Failed to create order:", err);
          }
        }
      }
    } catch (error) {
      toast({
        description: "An error occurred during payment",
        variant: "destructive",
      });
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-2xl">Your order</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Order Items */}
          <div className="space-y-4">
            <div className="flex justify-between text-sm font-medium">
              <span>Product</span>
              <span>Total</span>
            </div>
            {items.map((item, index) => (
              <div key={index} className="flex justify-between text-sm">
                <span>
                  {item.name} × {item.quantity}
                </span>
                <span>₹{(item.price - item.discount).toFixed(2)}</span>
              </div>
            ))}
          </div>

          <Separator />

          {/* Subtotal */}
          <div className="flex justify-between text-sm">
            <span>Cart Subtotal</span>
            <span>₹{subtotal.toFixed(2)}</span>
          </div>

          {/* Shipping */}
          <div className="flex justify-between text-sm">
            <span>Shipping</span>
            <span>Flat Rate: ₹{shippingCost.toFixed(2)}</span>
          </div>

          {/* Total */}
          <div className="flex justify-between text-lg font-semibold">
            <span>Order Total</span>
            <span>₹{total.toFixed(2)}</span>
          </div>

          <Separator />

          {/* Payment Form */}
          <PaymentForm
            handleOrderSubmit={handleOrderSubmit}
            stripe={stripe}
            isLoading={isLoading}
            error={error}
          />
        </div>
      </CardContent>
    </Card>
  );
}
