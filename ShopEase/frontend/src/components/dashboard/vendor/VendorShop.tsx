import CustomBreadcrumb from "@/components/shared/CustomBreadcrumb";
import AddShopSection from "./Shop/AddShopSection";
import { useGetShopQuery } from "@/redux/api/shopApi";
import ShopDetailsComponent from "./Shop/ShopDetailsComponent";

const VendorShop = () => {
  const { data } = useGetShopQuery();

  return (
    <div className="">
      <CustomBreadcrumb
        items={[
          { label: "Home", path: "/" },
          { label: "Dashboard", path: "/dashboard/vendor" },
          { label: "Shop" },
        ]}
        title="Shop Page"
      />
      <div>
        {!data ? <AddShopSection /> : <ShopDetailsComponent data={data} />}
      </div>
    </div>
  );
};

export default VendorShop;
