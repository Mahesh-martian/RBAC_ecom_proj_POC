"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { Store } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { ShopRouteShopData } from "@/types";

interface ShopCardProps {
  shop: ShopRouteShopData;
}

export function ShopCard({ shop }: ShopCardProps) {
  const router = useRouter();

  return (
    <Card className="flex flex-col h-full">
      <CardHeader className="flex-row gap-4 items-center">
        <div className="relative w-16 h-16 rounded-full overflow-hidden">
          <Image
            src={shop.logo}
            alt={`${shop.name} logo`}
            fill
            className="object-cover"
          />
        </div>
        <div>
          <h3 className="text-lg font-semibold">{shop.name}</h3>
          <p className="text-sm text-muted-foreground">{shop.description}</p>
        </div>
      </CardHeader>
      <CardContent className="flex-1">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-muted rounded-lg">
            <Store className="w-4 h-4 mx-auto mb-1" />
            <p className="text-sm font-medium">{shop.productsQuantity}</p>
            <p className="text-xs text-muted-foreground">Products</p>
          </div>
          <div className="text-center p-3 bg-muted rounded-lg">
            <p className="text-sm font-medium">{shop.followers}</p>
            <p className="text-xs text-muted-foreground">Followers</p>
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <Button
          className="w-full"
          onClick={() => router.push(`/shop-detail/${shop.shopId}`)}
        >
          Visit Shop
        </Button>
      </CardFooter>
    </Card>
  );
}
