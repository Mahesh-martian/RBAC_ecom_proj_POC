import { useState } from "react";
import CustomButton from "@/components/shared/CustomButton";
import { H2 } from "@/components/shared/CustomTypography";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import AddShopForm from "@/components/forms/AddShopForm";

const AddShopSection = () => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  return (
    <div>
      <div className="flex justify-end items-center mr-10 mt-10">
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <CustomButton
              className="bg-primary dark:bg-primary-foreground text-black dark:text-white dark:hover:text-black "
              onClick={() => setIsDialogOpen(true)}
            >
              Add Shop
            </CustomButton>
          </DialogTrigger>
          <AddShopForm onClose={() => setIsDialogOpen(false)} />
        </Dialog>
      </div>
      <div className="flex flex-col justify-center items-center mt-32 mx-10">
        <H2 className="text-center text-accent-foreground">
          You do not have any shop yet.
        </H2>
        <H2>Create your shop Now.</H2>
      </div>
    </div>
  );
};

export default AddShopSection;
