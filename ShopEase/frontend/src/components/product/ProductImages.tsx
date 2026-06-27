import { SingleProductData } from "@/types";
import Image from "next/image";
import React, { useState } from "react";

const ProductImages = ({ product }: { product: SingleProductData }) => {
  const [selectedImage, setSelectedImage] = useState(0);
  return (
    <div className="space-y-4">
      <div className="relative aspect-square">
        <Image
          src={product.image[selectedImage]}
          alt={`Product image ${selectedImage + 1}`}
          fill
          className="object-cover rounded-lg"
        />
      </div>
      <div className="flex gap-4">
        {product.image.map((image, index) => (
          <button
            key={index}
            onClick={() => setSelectedImage(index)}
            className={`relative w-24 aspect-square border rounded-md overflow-hidden ${
              selectedImage === index ? "ring-2 ring-primary" : ""
            }`}
          >
            <Image
              src={image}
              alt={`Product thumbnail ${index + 1}`}
              fill
              className="object-cover"
            />
          </button>
        ))}
      </div>
    </div>
  );
};

export default ProductImages;
