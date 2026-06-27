import React from "react";
import CustomInput from "../shared/CustomInput";
import CustomButton from "../shared/CustomButton";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

const editCategorySchema = z.object({
  name: z.string().min(3, "Name must be at least 3 characters long."),
  description: z
    .string()
    .min(10, "Description must be at least 10 characters long."),
});

export type EditCategoryFormValues = z.infer<typeof editCategorySchema>;

const EditCategoryForm = ({
  category,
  onSubmit,
  isLoading,
}: {
  category: { id: string; name: string; description: string };
  onSubmit: (data: EditCategoryFormValues) => void;
  isLoading: boolean;
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EditCategoryFormValues>({
    resolver: zodResolver(editCategorySchema),
    defaultValues: {
      name: category.name,
      description: category.description,
    },
  });
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <CustomInput
        placeholder="Category Name"
        label="Name *"
        inputClassName="bg-white py-4 focus-visible:ring-0 dark:text-black"
        {...register("name")}
        error={errors.name?.message}
      />

      <CustomInput
        placeholder="Category Description"
        label="Description *"
        inputClassName="bg-white py-4 focus-visible:ring-0 dark:text-black"
        {...register("description")}
        error={errors.description?.message}
      />

      <div className="mt-4">
        <CustomButton
          type="submit"
          className="bg-primary text-black"
          loading={isLoading}
        >
          Update Category
        </CustomButton>
      </div>
    </form>
  );
};

export default EditCategoryForm;
