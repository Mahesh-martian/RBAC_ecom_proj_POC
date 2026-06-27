import CustomButton from "@/components/shared/CustomButton";
import { useToast } from "@/hooks/use-toast";
import { useCreateCategoryMutation } from "@/redux/api/categoryApi";
import { useForm } from "react-hook-form";

const AddCategoryModal = ({ onClose }: { onClose: () => void }) => {
  const { toast } = useToast();
  const [createCategory, { isLoading }] = useCreateCategoryMutation();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<{ name: string; description: string }>();

  const onSubmit = async (data: { name: string; description: string }) => {
    try {
      const response = await createCategory(data).unwrap();
      toast({ description: `Category "${response.name}" created successfully!` });
      reset();
      onClose();
    } catch (error) {
      console.error("Error creating category:", error);
      toast({
        description: "Failed to create category. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className="block text-sm font-medium">Category Name</label>
        <input
          type="text"
          {...register("name", { required: "Category name is required" })}
          className="w-full p-2 border rounded-md"
        />
        {errors.name && <p className="text-red-500 text-sm">{errors.name.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium">Description</label>
        <textarea
          {...register("description", {
            required: "Description is required",
          })}
          className="w-full p-2 border rounded-md"
        ></textarea>
        {errors.description && (
          <p className="text-red-500 text-sm">{errors.description.message}</p>
        )}
      </div>

      <div className="flex justify-end space-x-2">
        <CustomButton
          type="button"
          onClick={onClose}
          className="bg-gray-300 text-black hover:bg-gray-400"
        >
          Cancel
        </CustomButton>
        <CustomButton
          type="submit"
          className="bg-primary text-white"
          loading={isLoading}
        >
          Add Category
        </CustomButton>
      </div>
    </form>
  );
};

export default AddCategoryModal;