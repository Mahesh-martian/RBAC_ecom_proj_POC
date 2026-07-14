"use client";
import React from "react";
import { FaArrowRightLong, FaRegEnvelope } from "react-icons/fa6";
import { IoKeyOutline } from "react-icons/io5";
import CustomInput from "@/components/shared/CustomInput";
import { CgRename } from "react-icons/cg";
import Link from "next/link";
import CustomButton from "@/components/shared/CustomButton";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Paragraph, H6 } from "@/components/shared/CustomTypography";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { SignUpData, signUpSchema } from "@/schemas/signUpSchema";
import { useRegisterMutation } from "@/redux/api/authApi";
import { useToast } from "@/hooks/use-toast";
import { useRouter } from "next/navigation";

const SignUpForm = () => {
  const [registerUser, { isLoading }] = useRegisterMutation();
  const { toast } = useToast();
  const router = useRouter();
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<SignUpData>({
    resolver: zodResolver(signUpSchema),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      role: undefined,
    },
  });

  const onSubmit = async (data: SignUpData) => {
    try {
      const response = await registerUser(data).unwrap();
      toast({
        description: `${response.message}`,
      });
      router.push("/sign-in");
    } catch (err) {
      console.error("Error from Backend:", err);
    }
  };
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <CustomInput
        icon={<CgRename />}
        placeholder="Name"
        inputClassName="border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground py-8"
        {...register("name")}
        error={errors.name?.message as string | undefined}
      />

      <CustomInput
        icon={<FaRegEnvelope />}
        placeholder="Email Address"
        type="email"
        inputClassName="border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground py-8"
        {...register("email")}
        error={errors.email?.message as string | undefined}
      />

      <CustomInput
        icon={<IoKeyOutline />}
        placeholder="Password"
        type="password"
        inputClassName="border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground py-8"
        {...register("password")}
        error={errors.password?.message as string | undefined}
      />

      <div className="flex justify-start items-center gap-5">
        <H6 className="font-semibold ">Account Type</H6>
        <Controller
          name="role"
          control={control}
          rules={{ required: "Role is required" }}
          render={({ field }) => (
            <RadioGroup
              {...field}
              onValueChange={(value) => field.onChange(value)}
              className="flex justify-center items-center gap-5"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="CUSTOMER" id="customer" />
                <label
                  htmlFor="customer"
                  className="text-sm font-medium  text-foreground dark:text-muted-foreground"
                >
                  Customer
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="VENDOR" id="vendor" />
                <label
                  htmlFor="vendor"
                  className="text-sm font-medium  text-foreground dark:text-muted-foreground"
                >
                  Vendor
                </label>
              </div>
            </RadioGroup>
          )}
        />
      </div>
      {errors.role && (
        <p className="text-red-500 text-sm">{errors.role.message}</p>
      )}

      <Link href="/sign-in">
        <Paragraph className="underline font-normal py-5 text-black hover:text-primary">
          Already Have Account?
        </Paragraph>
      </Link>

      <CustomButton
        className="bg-gradient-to-r from-primary to-accent dark:from-yellow-500 dark:to-yellow-600 w-full py-8 rounded-md shadow-md text-foreground hover:bg-black dark:hover:bg-white hover:text-white dark:hover:text-black gap-2 text-lg"
        icon={<FaArrowRightLong />}
        iconPosition="right"
        type="submit"
        loading={isLoading}
      >
        {isLoading ? "Registering" : "Register Now"}
      </CustomButton>
    </form>
  );
};

export default SignUpForm;
