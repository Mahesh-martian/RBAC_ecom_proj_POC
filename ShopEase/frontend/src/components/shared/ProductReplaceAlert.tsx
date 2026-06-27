import React from "react";
import { Button } from "../ui/button";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../ui/alert-dialog";

interface ProductReplaceAlertProps {
  isDialogOpen: boolean;
  setIsDialogOpen: React.Dispatch<React.SetStateAction<boolean>>;
  handleReplaceCart: () => void;
  handleCancelAddition: () => void;
}

const ProductReplaceAlert: React.FC<ProductReplaceAlertProps> = ({
  isDialogOpen,
  setIsDialogOpen,
  handleReplaceCart,
  handleCancelAddition,
}) => {
  return (
    <AlertDialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Vendor Mismatch</AlertDialogTitle>
          <AlertDialogDescription>
            You already have products from a different vendor in your cart. Do
            you want to replace your cart with this product?
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <Button
            variant="destructive"
            onClick={handleReplaceCart}
            className="bg-red-500"
          >
            Replace Cart
          </Button>
          <Button
            variant="outline"
            onClick={handleCancelAddition}
            className="bg-gray-200"
          >
            Cancel
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default ProductReplaceAlert;
