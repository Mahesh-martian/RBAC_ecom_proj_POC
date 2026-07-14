import CustomBreadcrumb from "@/components/shared/CustomBreadcrumb";
import { DataTable } from "@/components/shared/DataTable";
import {
  useDuplicateProductMutation,
  useGetVendorProductsQuery,
} from "@/redux/api/productApi";
import React, { useState } from "react";
import { vendorProductTableColumns } from "@/components/shared/tableColumnDef/VendorProductTableColumns";
import { VendorProductActions, VendorProductData } from "@/types";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import EditProduct from "./Product/EditProduct";
import { useToast } from "@/hooks/use-toast";
import DuplicationAlert from "./Product/DuplicationAlert";
import Heading from "@/components/shared/CustomHeading";
import CustomButton from "@/components/shared/CustomButton";
import AddProductForm from "@/components/forms/AddProductForm";
import FlashSaleModal from "./Product/FlashSaleModal";

const VendorProducts = () => {
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isAddProductDialogOpen, setIsAddProductDialogOpen] = useState(false);
  const [isFlashSaleOpen, setIsFlashSaleOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] =
    useState<VendorProductActions | null>(null);
  const { data } = useGetVendorProductsQuery({ page, limit });
  const [duplicateProduct, { isLoading }] = useDuplicateProductMutation();
  const [isAlertOpen, setIsAlertOpen] = useState(false);
  const { toast } = useToast();

  const handleFlashSale = (product: VendorProductData) => {
    const productWithActions: VendorProductActions = {
      ...product,
      handleEdit: () => handleEdit(product),
      handleDuplicate: () => handleDuplicate(),
      handleFlashSale: () => handleFlashSale(product),
    };
    setSelectedProduct(productWithActions);
    setIsFlashSaleOpen(true);
  };

  const handleEdit = (product: VendorProductData) => {
    const productWithActions: VendorProductActions = {
      ...product,
      handleEdit: () => handleEdit(product),
      handleDuplicate: () => handleDuplicate(),
      handleFlashSale: () => handleFlashSale(product),
    };
    setSelectedProduct(productWithActions);
    setIsEditOpen(true);
  };

  const handleDuplicate = async () => {
    if (selectedProduct) {
      try {
        const response = await duplicateProduct({
          productId: selectedProduct.productId,
        });

        if (response && response.data && response.data.success) {
          toast({
            description: `${response.data.message}`,
          });
        } else {
          toast({
            description: `An Error Occurred`,
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error("Error duplicating product:", error);
      }
    }
    setIsAlertOpen(false);
  };

  const tableData: VendorProductActions[] =
    data?.data.map((product: VendorProductData) => ({
      ...product,
      handleEdit: () => handleEdit(product),
      handleDuplicate: async () => {
        // Ensure it is async
        const productWithActions: VendorProductActions = {
          ...product,
          handleEdit: () => handleEdit(product),
          handleDuplicate: async () => handleDuplicate(), // Make this async
          handleFlashSale: () => handleFlashSale(product),
        };
        setSelectedProduct(productWithActions); // Pass a valid VendorProductActions object
        setIsAlertOpen(true); // Open the confirmation dialog
      },
      handleFlashSale: () => handleFlashSale(product),
    })) || [];

  const totalPages = Math.ceil((data?.meta?.total || 0) / limit);

  const handlePreviousPage = () => {
    if (page > 1) setPage((prev) => prev - 1);
  };

  const handleNextPage = () => {
    if (page < totalPages) setPage((prev) => prev + 1);
  };

  return (
    <div>
      <CustomBreadcrumb
        items={[
          { label: "Home", path: "/" },
          { label: "Dashboard", path: "/dashboard/vendor" },
          { label: "Product" },
        ]}
        title="Product Page"
      />
      <div className="px-5 pb-10">
        <div className="flex justify-center items-center pt-10 pb-5">
          <Heading text="Your Products" className="text-4xl lg:text-6xl" />
        </div>
        <div className="flex justify-end items-center mr-10 my-5">
          <Dialog
            open={isAddProductDialogOpen}
            onOpenChange={setIsAddProductDialogOpen}
          >
            <DialogTrigger asChild>
              <CustomButton
                className="bg-primary dark:bg-primary-foreground text-black dark:text-white dark:hover:text-black "
                onClick={() => setIsAddProductDialogOpen(true)}
              >
                Add Product
              </CustomButton>
            </DialogTrigger>
            <AddProductForm onClose={() => setIsAddProductDialogOpen(false)} />
          </Dialog>
        </div>
        {data && (
          <DataTable
            data={tableData}
            columns={vendorProductTableColumns}
            pageIndex={page}
            totalPages={totalPages}
            onPreviousPage={handlePreviousPage}
            onNextPage={handleNextPage}
          />
        )}
      </div>
      {isEditOpen && selectedProduct && (
        <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
          <EditProduct
            product={selectedProduct}
            onClose={() => setIsEditOpen(false)}
          />
        </Dialog>
      )}
      {isAlertOpen && (
        <DuplicationAlert
          isAlertOpen={isAlertOpen}
          setIsAlertOpen={setIsAlertOpen}
          handleDuplicate={handleDuplicate}
          isLoading={isLoading}
        />
      )}
      {isFlashSaleOpen && (
        <Dialog open={isFlashSaleOpen} onOpenChange={setIsFlashSaleOpen}>
          <FlashSaleModal
            productId={selectedProduct?.productId || ""}
            onClose={() => setIsFlashSaleOpen(false)}
          />
        </Dialog>
      )}
    </div>
  );
};

export default VendorProducts;
