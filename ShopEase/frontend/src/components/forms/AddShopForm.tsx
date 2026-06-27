"use client";
import {
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import CustomButton from "@/components/shared/CustomButton";
import CustomInput from "../shared/CustomInput";
import { CgRename } from "react-icons/cg";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useCreateShopMutation } from "@/redux/api/shopApi";
import { useToast } from "@/hooks/use-toast";

// Define Zod schema
const addShopSchema = z.object({
  shopName: z.string().min(3, "Shop name must be at least 3 characters long."),
  shopDescription: z
    .string()
    .min(10, "Description must be at least 10 characters long."),
  shopLogo: z.custom<FileList>(
    (value) =>
      typeof window !== "undefined" &&
      value instanceof FileList &&
      value.length === 1,
    { message: "Please upload exactly one logo." },
  ),
});

type AddShopFormValues = z.infer<typeof addShopSchema>;
const AddShopForm = ({ onClose }: { onClose: () => void }) => {
  const [createShop, { isLoading }] = useCreateShopMutation();
  const { toast } = useToast();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AddShopFormValues>({
    resolver: zodResolver(addShopSchema),
  });

  const onSubmit = async (data: AddShopFormValues) => {
    const logoFile = data.shopLogo[0];

    const response = await createShop({
      name: data.shopName,
      description: data.shopDescription,
      file: logoFile,
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
    <DialogContent className="text-card-foreground">
      <DialogHeader>
        <DialogTitle className="">Create a New Shop</DialogTitle>
        <DialogDescription>
          Fill in the details below to create your shop.
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Shop Name */}
        <CustomInput
          icon={<CgRename />}
          placeholder="Shop Name"
          label="Shop Name"
          inputClassName="bg-white py-4 focus-visible:ring-0 dark:text-black"
          {...register("shopName")}
          error={errors.shopName?.message}
        />

        {/* Shop Description */}
        <CustomInput
          icon={<CgRename />}
          placeholder="Description"
          label="Description"
          inputClassName="bg-white py-4 focus-visible:ring-0 dark:text-black"
          {...register("shopDescription")}
          error={errors.shopDescription?.message}
        />

        {/* Shop Logo */}
        <CustomInput
          placeholder="Logo"
          label="Logo"
          inputClassName="bg-white pb-3 focus-visible:ring-0"
          type="file"
          {...register("shopLogo")}
          error={errors.shopLogo?.message}
        />

        {/* Submit Button */}
        <div className="mt-4">
          <CustomButton
            type="submit"
            className="bg-primary text-black"
            loading={isLoading}
          >
            Create Shop
          </CustomButton>
        </div>
      </form>
    </DialogContent>
  );
};

export default AddShopForm;
