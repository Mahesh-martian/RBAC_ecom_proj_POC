import React, { useState } from "react";
import FeatureCard from "./FeatureCard";
import { features, randomColors, randomTags } from "@/constants";
import { Separator } from "../ui/separator";
import { Button } from "../ui/button";
import { ShoppingBag } from "lucide-react";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { RadioGroup, RadioGroupItem } from "../ui/radio-group";
import { Badge } from "../ui/badge";
import { SingleProductData } from "@/types";
import { useDispatch, useSelector } from "react-redux";
import { addToCart, replaceCart } from "@/redux/slices/cartSlice";
import { useToast } from "@/hooks/use-toast";
import { RootState } from "@/redux/store";
import Link from "next/link";
import ProductReplaceAlert from "../shared/ProductReplaceAlert";

interface ProductInfoProps {
  product: SingleProductData;
  quantity: number;
  setQuantity: React.Dispatch<React.SetStateAction<number>>;
  renderStars: (rating: number) => JSX.Element[];
}

const ProductInfo: React.FC<ProductInfoProps> = ({
  product,
  quantity,
  setQuantity,
  renderStars,
}) => {
  const { shopId } = product;
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const averageRating = product.reviews
    ? Math.round(
        product.reviews.reduce((sum, review) => sum + review.rating, 0) /
          product.reviews.length,
      )
    : 0;

  const productTags = randomTags.slice(0, 3);
  const dispatch = useDispatch();
  const { toast } = useToast();

  const cartItems = useSelector((state: RootState) => state.cart.items);

  const handleAddToCart = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault(); // Prevent navigating to the product page
    if (cartItems.length > 0 && cartItems[0].shopId !== shopId) {
      setIsDialogOpen(true); // Open the dialog for vendor mismatch
      return;
    }

    // If no vendor conflict, add the product
    dispatch(addToCart({ product, quantity: 1 }));
    toast({
      description: `${name} successfully added to the cart!`,
    });
  };

  const handleReplaceCart = () => {
    dispatch(replaceCart({ product, quantity: 1 })); // Replace the cart
    toast({
      description: `${name} successfully added to the cart!`,
    });
    setIsDialogOpen(false); // Close the dialog
  };

  const handleCancelAddition = () => {
    toast({
      description: "The product was not added to the cart.",
      variant: "destructive",
    });
    setIsDialogOpen(false); // Close the dialog
  };

  return (
    <div className="space-y-6">
      <div>
        <Badge>{product.category?.name || "Unknown Category"}</Badge>
        <div className="flex items-center gap-4 mt-2">
          <h1 className="text-3xl font-bold">{product.name}</h1>
          <Badge variant="secondary" className="bg-green-100 text-green-800">
            {product.inventory > 0 ? "In Stock" : "Out of Stock"}
          </Badge>
        </div>
        <div className="flex items-center gap-2 mt-2">
          {renderStars(averageRating)}
          <span className="text-muted-foreground">
            ({product.reviews?.length || 0} Reviews)
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-3xl font-bold text-primary">
          ₹{product.price}
        </span>
        {product.discount > 0 && (
          <span className="text-xl text-muted-foreground line-through">
            ₹{(product.price * (1 + product.discount / 100)).toFixed(2)}
          </span>
        )}
      </div>

      <p className="text-muted-foreground">{product.description}</p>

      <div className="space-y-4">
        <div>
          <Label>Color</Label>
          <RadioGroup
            defaultValue={randomColors[0]}
            className="flex gap-2 mt-2"
          >
            {randomColors.map((color) => (
              <RadioGroupItem
                key={color}
                value={color}
                id={color}
                className={`w-6 h-6 rounded-full bg-${color}-500`}
              />
            ))}
          </RadioGroup>
        </div>

        <div>
          <Label htmlFor="quantity">Quantity</Label>
          <Input
            id="quantity"
            type="number"
            min="1"
            value={quantity}
            onChange={(e) => setQuantity(parseInt(e.target.value))}
            className="w-24 mt-2"
          />
        </div>

        <div className="flex gap-4">
          <Button size="lg" className="flex-1" onClick={handleAddToCart}>
            Add to Cart
          </Button>
          <Button size="lg" variant="outline">
            <Link href={`/shop-detail/${product.shopId}`}>
              <ShoppingBag className="w-4 h-4" />
            </Link>
          </Button>
        </div>
      </div>

      <Separator />

      <div className="grid grid-cols-3 gap-4">
        {features.map((feature, index) => (
          <FeatureCard key={index} Icon={feature.Icon} text={feature.text} />
        ))}
      </div>

      <div>
        <span className="text-sm text-muted-foreground">SKU: </span>
        <span className="text-sm">{product.productId}</span>
      </div>

      <div>
        <span className="text-sm text-muted-foreground">Tags: </span>
        <span className="text-sm">{productTags.join(", ")}</span>
      </div>
      {isDialogOpen && (
        <ProductReplaceAlert
          isDialogOpen={isDialogOpen}
          setIsDialogOpen={setIsDialogOpen}
          handleReplaceCart={handleReplaceCart}
          handleCancelAddition={handleCancelAddition}
        />
      )}
    </div>
  );
};

export default ProductInfo;
