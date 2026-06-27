"use client";

import { Elements } from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";
import { useSelector } from "react-redux";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import CheckoutCard from "./CheckoutCard";

const stripePromise = loadStripe(
  process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!,
);

export default function CheckoutContent() {
  const router = useRouter();
  const user = useSelector((state: any) => state.auth.user);

  useEffect(() => {
    if (!user) {
      router.push("/sign-in");
    }
  }, [user, router]);

  if (!user) {
    return null;
  }

  return (
    <Elements stripe={stripePromise}>
      <CheckoutCard />
    </Elements>
    // <div className="pt-32 mt-20">You are in the checkout page</div>
  );
}

{
  /* <Elements stripe={stripePromise}>
      <CheckoutForm userId={user.userId} />
    </Elements> */
}
