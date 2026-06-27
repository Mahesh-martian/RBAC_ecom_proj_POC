"use client";

import { useRouter } from "next/navigation";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { selectButtonCategories } from "@/constants";
import { Control, Controller } from "react-hook-form";

interface CategorySelectOptionProps {
  isForm?: boolean;
  control?: Control<any>;
  error?: string;
}

const CategorySelectOption = ({
  isForm,
  control,
  error,
}: CategorySelectOptionProps) => {
  const router = useRouter();

  if (isForm && control) {
    return (
      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium">Category</label>
        <Controller
          name="categoryId"
          control={control}
          render={({ field }) => (
            <Select onValueChange={field.onChange}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select Category" />
              </SelectTrigger>
              <SelectContent>
                {selectButtonCategories.map((category) => (
                  <SelectItem key={category.id} value={category.id}>
                    {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
        {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-4 mb-4 pb-5">
      <Select
        onValueChange={(value) =>
          router.push(`/all-products?categoryId=${value}`)
        }
      >
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Select Category" />
        </SelectTrigger>
        <SelectContent>
          {selectButtonCategories.map((category) => (
            <SelectItem key={category.id} value={category.id}>
              {category.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};

export default CategorySelectOption;
