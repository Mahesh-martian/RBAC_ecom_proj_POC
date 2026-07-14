"use client";

import Image from "next/image";
import { useState } from "react";

interface ProductData {
  id: string;
  name: string;
  price: number;
  description: string;
  images: string[];
  rating: number;
}

interface ProductDetailsClientProps {
  product: ProductData;
}

export default function ProductDetailsClient({
  product,
}: ProductDetailsClientProps) {
  const [selectedImage, setSelectedImage] = useState(0);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid md:grid-cols-2 gap-8">
        {/* Product Images */}
        <div className="space-y-4">
          <div className="relative aspect-square">
            <Image
              src={product.images[selectedImage]}
              alt="Product image"
              fill
              className="object-cover rounded-lg"
            />
          </div>
          <div className="flex gap-4">
            {product.images.map((image, index) => (
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

        {/* Product Info */}
        <div className="space-y-6">
          <h1 className="text-3xl font-bold">{product.name}</h1>
          <div className="flex items-center gap-2">
            <span className="text-3xl font-bold text-primary">
              ₹{product.price.toFixed(2)}
            </span>
          </div>
          <p className="text-muted-foreground">{product.description}</p>
        </div>
      </div>
    </div>
  );
}
