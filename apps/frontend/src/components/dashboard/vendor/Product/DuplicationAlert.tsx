import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { DuplicationAlertProps } from "@/types";
import React from "react";

const DuplicationAlert: React.FC<DuplicationAlertProps> = ({
  isAlertOpen,
  setIsAlertOpen,
  handleDuplicate,
  isLoading,
}) => {
  return (
    <AlertDialog open={isAlertOpen} onOpenChange={setIsAlertOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Confirm Duplication</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to duplicate this product? This action cannot
            be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => setIsAlertOpen(false)}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction onClick={handleDuplicate} disabled={isLoading}>
            {isLoading ? "Duplicating..." : "Yes, Duplicate"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default DuplicationAlert;
