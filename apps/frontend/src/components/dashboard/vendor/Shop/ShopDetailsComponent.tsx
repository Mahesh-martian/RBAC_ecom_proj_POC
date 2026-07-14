import { H3, H4, Paragraph } from "@/components/shared/CustomTypography";
import { ShopData } from "@/types";

import Image from "next/image";

const ShopDetailsComponent = ({ data }: { data: ShopData }) => {
  return (
    <div className="p-10 space-y-5">
      <H3>Shop Name: {data?.name}</H3>
      <H4>Shop Id: {data?.shopId}</H4>
      <Paragraph className="text-primary-foreground">
        About the shop: {data?.description}
      </Paragraph>
      <Image
        src={data?.logo}
        alt="Shop logo"
        height={100}
        width={100}
        className="object-cover"
      />
    </div>
  );
};

export default ShopDetailsComponent;
