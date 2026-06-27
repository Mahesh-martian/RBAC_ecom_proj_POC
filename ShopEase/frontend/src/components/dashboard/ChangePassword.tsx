"use client";
import React from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import CustomInput from "@/components/shared/CustomInput";
import CustomButton from "@/components/shared/CustomButton";
import { useToast } from "@/hooks/use-toast";
import { useChangePasswordMutation } from "@/redux/api/authApi";

// Define schema for validation using zod
const changePasswordSchema = z
  .object({
    oldPassword: z
      .string()
      .min(6, { message: "Old password must be at least 6 characters long" }),
    newPassword: z
      .string()
      .min(6, { message: "New password must be at least 6 characters long" }),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords must match",
    path: ["confirmPassword"],
  });

type ChangePasswordData = z.infer<typeof changePasswordSchema>;

const ChangePassword = () => {
  const [changePassword, { isLoading }] = useChangePasswordMutation();
  const { toast } = useToast();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ChangePasswordData>({
    resolver: zodResolver(changePasswordSchema),
  });

  const onSubmit = async (data: ChangePasswordData) => {
    try {
      const response = await changePassword({
        oldPassword: data.oldPassword,
        newPassword: data.newPassword,
      }).unwrap();
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
        Change Password
      </h1>
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="w-full max-w-md bg-white dark:bg-gray-800 p-6 rounded-md shadow-md space-y-4"
      >
        <CustomInput
          label="Old Password"
          placeholder="Enter your old password"
          type="password"
          {...register("oldPassword")}
          error={errors.oldPassword?.message}
        />

        <CustomInput
          label="New Password"
          placeholder="Enter your new password"
          type="password"
          {...register("newPassword")}
          error={errors.newPassword?.message}
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
          {isLoading ? "Changing..." : "Change Password"}
        </CustomButton>
      </form>
    </div>
  );
};

export default ChangePassword;
