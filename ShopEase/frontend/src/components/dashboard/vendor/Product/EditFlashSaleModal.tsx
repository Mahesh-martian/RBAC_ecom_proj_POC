"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUpdateFlashSaleMutation } from "@/redux/api/flashSaleApi";
import CustomButton from "@/components/shared/CustomButton";
import { useToast } from "@/hooks/use-toast";

const flashSaleSchema = z.object({
  discount: z
    .number()
    .min(0, "Discount must be at least 0%")
    .max(100, "Discount cannot exceed 100%"),
});

type FlashSaleFormValues = z.infer<typeof flashSaleSchema>;

interface EditFlashSaleModalProps {
  isOpen: boolean;
  onClose: () => void;
  flashSale: {
    id: string;
    discount: number;
  };
}

const EditFlashSaleModal: React.FC<EditFlashSaleModalProps> = ({
  isOpen,
  onClose,
  flashSale,
}) => {
  const [updateFlashSale, { isLoading }] = useUpdateFlashSaleMutation();
  const { toast } = useToast();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FlashSaleFormValues>({
    resolver: zodResolver(flashSaleSchema),
    defaultValues: {
      discount: flashSale.discount,
    },
  });

  const onSubmit = async (data: FlashSaleFormValues) => {
    try {
      const response = await updateFlashSale({
        id: flashSale.id,
        updates: { discount: data.discount },
      }).unwrap();
      if (response.success) {
        toast({
          description: `${response.message}`,
        });
        onClose();
      } else {
        toast({
          description: "Failed to update flash sale.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error updating flash sale:", error);
    }
  };

  return isOpen ? (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded p-6 space-y-4 w-96">
        <h2 className="text-xl font-bold">Edit Flash Sale</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Discount (%)
            </label>
            <input
              type="number"
              {...register("discount", { valueAsNumber: true })}
              className="w-full border p-2 rounded"
            />
            {errors.discount && (
              <p className="text-red-500 text-sm">{errors.discount.message}</p>
            )}
          </div>
          <div className="flex justify-end space-x-2">
            <CustomButton onClick={onClose}>Cancel</CustomButton>
            <CustomButton
              type="submit"
              className="bg-primary text-black"
              loading={isLoading}
            >
              Save Changes
            </CustomButton>
          </div>
        </form>
      </div>
    </div>
  ) : null;
};

export default EditFlashSaleModal;
