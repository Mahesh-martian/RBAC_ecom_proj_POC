import React from "react";
import {
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import EditCategoryForm, {
  EditCategoryFormValues,
} from "@/components/forms/EditCategoryForm";

const EditCategoryInfoModal = ({
  category,
  onSubmit,
  isLoading,
}: {
  category: { id: string; name: string; description: string };
  onSubmit: (data: EditCategoryFormValues) => void;
  isLoading: boolean;
}) => {
  return (
    <DialogContent
      className="text-card-foreground"
      //  style={{ height: "90vh", overflowY: "auto" }}
    >
      <DialogHeader>
        <DialogTitle>Edit Category</DialogTitle>
        <DialogDescription>
          Update the Category details below.
        </DialogDescription>
      </DialogHeader>
      <EditCategoryForm
        category={category}
        onSubmit={onSubmit}
        isLoading={isLoading}
      />
    </DialogContent>
  );
};

export default EditCategoryInfoModal;
