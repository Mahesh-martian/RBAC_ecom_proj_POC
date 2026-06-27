import CustomBreadcrumb from "@/components/shared/CustomBreadcrumb";
import Heading from "@/components/shared/CustomHeading";
import { DataTable } from "@/components/shared/DataTable";
import { cartItemTableColumns } from "@/components/shared/tableColumnDef/CartItemTableColumn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import React from "react";
import { useSelector } from "react-redux";

const Cart = () => {
  const { items } = useSelector((state: any) => state.cart);
  return (
    <div>
      <CustomBreadcrumb
        items={[
          { label: "Home", path: "/" },
          { label: "Dashboard", path: "/dashboard/customer" },
          { label: "Cart" },
        ]}
        title="Cart Page"
      />
      <Heading
        text="Your Cart"
        className="text-4xl lg:text-6xl text-center py-20"
      />

      <div>
        <div className=" py-10 px-5 lg:px-10">
          <Card>
            <CardHeader>
              <CardTitle>Shopping Cart</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={cartItemTableColumns}
                data={items}
                pageIndex={1}
                totalPages={1}
                onPreviousPage={() => {}}
                onNextPage={() => {}}
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Cart;
