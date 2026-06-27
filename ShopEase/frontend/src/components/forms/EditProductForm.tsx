"use client";
import React from "react";
import CustomButton from "@/components/shared/CustomButton";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import CustomInput from "@/components/shared/CustomInput";
import { VendorProductActions } from "@/types";

import { useToast } from "@/hooks/use-toast";
import { useEditProductMutation } from "@/redux/api/productApi";

const editProductSchema = z.object({
  productName: z
    .string()
    .min(3, "Product name must be at least 3 characters long."),
  productDescription: z
    .string()
    .min(10, "Product description must be at least 10 characters long."),
  price: z.number().min(0, "Price must be a positive number."),
  discount: z.number().min(0).max(100, "Discount must be between 0 and 100."),
  inventory: z.number().min(0, "Inventory must be a positive number."),
  additionalImages: z.custom<FileList>(
    (value) =>
      typeof window !== "undefined" &&
      value instanceof FileList &&
      value.length >= 2 &&
      value.length <= 5,
    {
      message: "You must upload between 2 and 5 images.",
    },
  ),
});
type EditProductFormValues = z.infer<typeof editProductSchema>;

const EditProductForm = ({
  onClose,
  product,
}: {
  onClose: () => void;
  product: VendorProductActions;
}) => {
  const { toast } = useToast();
  const [editProduct, { isLoading }] = useEditProductMutation();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EditProductFormValues>({
    resolver: zodResolver(editProductSchema),
    defaultValues: {
      productName: product.name,
      productDescription: product.description,
      price:
        typeof product.price === "number"
          ? product.price
          : parseFloat(product.price),
      discount: product.discount,
      inventory: product.inventory,
    },
  });

  const onSubmit = async (data: EditProductFormValues) => {
    const uploadedImages = Array.from(data.additionalImages);
    const response = await editProduct({
      productId: product.productId,
      name: data.productName,
      description: data.productDescription,
      discount: data.discount,
      inventory: data.inventory,
      price: data.price,
      additionalImages: uploadedImages,
    }).unwrap();

    if (response.success) {
      toast({
        description: `${response.message}`,
      });
      onClose();
    } else {
      toast({
        description: `An Error Occurred`,
        variant: "destructive",
      });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Product Name */}
      <CustomInput
        placeholder="Product Name"
        label="Product Name *"
        inputClassName="bg-white py-4 focus-visible:ring-0 dark:text-black"
        {...register("productName")}
        error={errors.productName?.message}
      />

      {/* Product Description */}
      <CustomInput
        placeholder="Product Description"
        label="Description *"
        inputClassName="bg-white py-4 focus-visible:ring-0 dark:text-black"
        {...register("productDescription")}
        error={errors.productDescription?.message}
      />

      {/* Price */}
      <CustomInput
        placeholder="Price"
        label="Price *"
        type="number"
        step="0.01"
        inputClassName="bg-white py-4 focus-visible:ring-0 dark:text-black"
        {...register("price", { valueAsNumber: true })}
        error={errors.price?.message}
      />

      {/* Discount */}
      <CustomInput
        placeholder="Discount (%)"
        label="Discount *"
        type="number"
        inputClassName="bg-white py-4 focus-visible:ring-0 dark:text-black"
        {...register("discount", { valueAsNumber: true })}
        error={errors.discount?.message}
      />

      {/* Inventory */}
      <CustomInput
        placeholder="Inventory"
        label="Inventory *"
        type="number"
        inputClassName="bg-white py-4 focus-visible:ring-0 dark:text-black"
        {...register("inventory", { valueAsNumber: true })}
        error={errors.inventory?.message}
      />

      <CustomInput
        placeholder="Additional Images"
        label="Upload Images (2-5)"
        inputClassName="bg-white py-4 focus-visible:ring-0"
        type="file"
        multiple
        {...register("additionalImages")}
        error={errors.additionalImages?.message}
      />

      {/* Submit Button */}
      <div className="mt-4">
        <CustomButton
          type="submit"
          className="bg-primary text-black"
          loading={isLoading}
        >
          Save Changes
        </CustomButton>
      </div>
    </form>
  );
};

export default EditProductForm;
