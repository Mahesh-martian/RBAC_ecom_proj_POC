import React from "react";
import {
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import CreateFlashSaleForm from "@/components/forms/CreateFlashSaleForm";

interface FlashSaleModalProps {
  productId: string;
  onClose: () => void;
}

const FlashSaleModal: React.FC<FlashSaleModalProps> = ({
  productId,
  onClose,
}) => {
  return (
    <DialogContent
      className="text-card-foreground"
      style={{ height: "90vh", overflowY: "auto" }}
    >
      <DialogHeader>
        <DialogTitle>Create Flash Sale</DialogTitle>
      </DialogHeader>

      <CreateFlashSaleForm onClose={onClose} productId={productId} />
    </DialogContent>
  );
};

export default FlashSaleModal;
