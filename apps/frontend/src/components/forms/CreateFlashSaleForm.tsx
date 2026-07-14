"use client";

import React from "react";
import { useForm, Controller } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import CustomButton from "../shared/CustomButton";
import {
  CreateFlashSale,
  useCreateFlashSaleMutation,
} from "@/redux/api/flashSaleApi";
import { useToast } from "@/hooks/use-toast";
import { Calendar } from "@/components/ui/calendar";

const flashSaleSchema = z.object({
  discount: z.preprocess(
    (val) => Number(val),
    z
      .number({
        invalid_type_error: "Discount must be a number",
      })
      .min(0, "Discount must be greater than or equal to 0")
      .max(100, "Discount cannot exceed 100"),
  ),
  startTime: z.preprocess(
    (val) => (typeof val === "string" ? new Date(val) : val),
    z.date({
      required_error: "Start date is required",
      invalid_type_error: "Start date must be a valid date",
    }),
  ),
  endTime: z.preprocess(
    (val) => (typeof val === "string" ? new Date(val) : val),
    z.date({
      required_error: "End date is required",
      invalid_type_error: "End date must be a valid date",
    }),
  ),
});

type FlashSaleFormValues = z.infer<typeof flashSaleSchema>;

const CreateFlashSaleForm = ({
  onClose,
  productId,
}: {
  onClose: () => void;
  productId: string;
}) => {
  const { toast } = useToast();
  const [createFlashSale, { isLoading }] = useCreateFlashSaleMutation();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<FlashSaleFormValues>({
    resolver: zodResolver(flashSaleSchema),
    defaultValues: {
      discount: 0,
      startTime: new Date(),
      endTime: new Date(),
    },
  });

  const onSubmit = async (data: FlashSaleFormValues) => {
    const flashSale: CreateFlashSale = {
      productId,
      discount: data.discount,
      startTime: data.startTime.toISOString(),
      endTime: data.endTime.toISOString(),
    };

    try {
      const response = await createFlashSale(flashSale).unwrap();
      if (response.success) {
        toast({ description: "Flash sale created successfully!" });
        onClose();
      } else {
        toast({
          description: "Failed to create flash sale.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error creating flash sale:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Start Time */}
      <div>
        <label className="block text-sm font-medium mb-2">Start Time</label>
        <Controller
          name="startTime"
          control={control}
          render={({ field }) => (
            <Calendar
              mode="single"
              selected={field.value}
              onSelect={field.onChange}
              className="rounded-md border"
            />
          )}
        />
        {errors.startTime && (
          <p className="text-red-500 text-sm">{errors.startTime.message}</p>
        )}
      </div>

      {/* End Time */}
      <div>
        <label className="block text-sm font-medium mb-2">End Time</label>
        <Controller
          name="endTime"
          control={control}
          render={({ field }) => (
            <Calendar
              mode="single"
              selected={field.value}
              onSelect={field.onChange}
              className="rounded-md border"
            />
          )}
        />
        {errors.endTime && (
          <p className="text-red-500 text-sm">{errors.endTime.message}</p>
        )}
      </div>

      {/* Discount */}
      <div>
        <label className="block text-sm font-medium mb-2">Discount (%)</label>
        <Controller
          name="discount"
          control={control}
          render={({ field }) => (
            <input
              type="number"
              step="0.01"
              {...field}
              className="w-full border p-2 rounded"
            />
          )}
        />

        {errors.discount && (
          <p className="text-red-500 text-sm">{errors.discount.message}</p>
        )}
      </div>

      {/* Submit Button */}
      <div className="flex justify-end space-x-2">
        <CustomButton onClick={onClose} type="button">
          Cancel
        </CustomButton>
        <CustomButton
          type="submit"
          disabled={isLoading}
          className="bg-primary text-white"
        >
          Submit
        </CustomButton>
      </div>
    </form>
  );
};

export default CreateFlashSaleForm;
