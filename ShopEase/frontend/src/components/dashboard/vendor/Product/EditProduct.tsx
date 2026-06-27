import EditProductForm from "@/components/forms/EditProductForm";
import {
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { VendorProductActions } from "@/types";

const EditProduct = ({
  onClose,
  product,
}: {
  onClose: () => void;
  product: VendorProductActions;
}) => {
  return (
    <DialogContent
      className="text-card-foreground"
      style={{ height: "90vh", overflowY: "auto" }}
    >
      <DialogHeader>
        <DialogTitle>Edit Product</DialogTitle>
        <DialogDescription>Update the product details below.</DialogDescription>
      </DialogHeader>
      <EditProductForm onClose={onClose} product={product} />
    </DialogContent>
  );
};

export default EditProduct;
