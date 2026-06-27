"use client";
import React from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import CustomInput from "@/components/shared/CustomInput";
import CustomButton from "@/components/shared/CustomButton";
import { useToast } from "@/hooks/use-toast";
import { useForgotPasswordMutation } from "@/redux/api/authApi";

// Define schema for validation using zod
const forgotPasswordSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
});

type ForgotPasswordData = z.infer<typeof forgotPasswordSchema>;

const ForgotPassword = () => {
  const [forgotPassword, { isLoading }] = useForgotPasswordMutation();
  const { toast } = useToast();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordData) => {
    try {
      const response = await forgotPassword(data).unwrap();
      toast({
        description: response.message,
      });
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
        Forgot Password
      </h1>
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="w-full max-w-md bg-white dark:bg-gray-800 p-6 rounded-md shadow-md space-y-4"
      >
        <CustomInput
          label="Email Address"
          placeholder="Enter your email"
          type="email"
          {...register("email")}
          error={errors.email?.message}
        />

        <CustomButton
          className="w-full bg-gradient-to-r from-primary to-accent py-3 rounded-md shadow-md text-white"
          type="submit"
          loading={isLoading}
        >
          {isLoading ? "Sending..." : "Send Reset Link"}
        </CustomButton>
      </form>
    </div>
  );
};

export default ForgotPassword;
