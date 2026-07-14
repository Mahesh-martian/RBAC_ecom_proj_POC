"use client";
import React, { Suspense, useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter, useSearchParams } from "next/navigation";
import CustomInput from "@/components/shared/CustomInput";
import CustomButton from "@/components/shared/CustomButton";
import { useToast } from "@/hooks/use-toast";
import { useResetPasswordMutation } from "@/redux/api/authApi";

// Define schema for validation using zod
const resetPasswordSchema = z
  .object({
    password: z
      .string()
      .min(8, { message: "Password must be at least 8 characters long" }),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords must match",
    path: ["confirmPassword"],
  });

type ResetPasswordData = z.infer<typeof resetPasswordSchema>;

const ResetPasswordComponent = () => {
  const [resetPassword, { isLoading }] = useResetPasswordMutation();
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const router = useRouter();
  const userId = searchParams.get("userId");
  const token = searchParams.get("token");

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordData>({
    resolver: zodResolver(resetPasswordSchema),
  });

  useEffect(() => {
    if (!userId || !token) {
      toast({
        description: "Invalid or missing reset token",
        variant: "destructive",
      });
    }
  }, [userId, token, toast]);

  const onSubmit = async (data: ResetPasswordData) => {
    if (!userId || !token) return;

    try {
      const response = await resetPassword({
        id: userId,
        password: data.password,
        token, // This is passed to the headers in the query
      }).unwrap();
      toast({
        description: response.message,
      });
      router.push("/sign-in");
    } catch (err: any) {
      toast({
        description: err?.data?.message || "Something went wrong",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
      <h1 className="text-2xl font-bold text-center mb-6 text-foreground dark:text-muted-foreground">
        Reset Password
      </h1>
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="w-full max-w-md bg-white dark:bg-gray-800 p-6 rounded-md shadow-md space-y-4"
      >
        <CustomInput
          label="New Password"
          placeholder="Enter your new password"
          type="password"
          {...register("password")}
          error={errors.password?.message}
        />

        <CustomInput
          label="Confirm Password"
          placeholder="Confirm your new password"
          type="password"
          {...register("confirmPassword")}
          error={errors.confirmPassword?.message}
        />

        <CustomButton
          className="w-full bg-gradient-to-r from-primary to-accent py-3 rounded-md shadow-md text-white"
          type="submit"
          loading={isLoading}
        >
          {isLoading ? "Resetting..." : "Reset Password"}
        </CustomButton>
      </form>
    </div>
  );
};

export default function ResetPassword() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ResetPasswordComponent />
    </Suspense>
  );
}
