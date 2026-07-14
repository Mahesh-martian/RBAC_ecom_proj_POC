"use client";

import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useRouter, useSearchParams } from "next/navigation";
import React, { useState } from "react";

const ProductFilters = () => {
  const router = useRouter();
  const searchParams = useSearchParams();

  // States for filters
  const [priceRange, setPriceRange] = useState<number[]>([0, 500]);
  const [discountRange, setDiscountRange] = useState<number[]>([0, 100]);
  const [sortOption, setSortOption] = useState<string>("price-asc");

  // Handle Filter and Sort Apply
  const applyFilters = () => {
    const params = new URLSearchParams();

    // Add existing search params
    searchParams.forEach((value, key) => {
      params.set(key, value);
    });

    // Update with new filters
    params.set("minPrice", String(priceRange[0]));
    params.set("maxPrice", String(priceRange[1]));
    params.set("minDiscount", String(discountRange[0]));
    params.set("maxDiscount", String(discountRange[1]));

    // Sorting
    const [sortBy, sortOrder] = sortOption.split("-");
    params.set("sortBy", sortBy);
    params.set("sortOrder", sortOrder);

    // Navigate with updated query
    router.push(`/all-products?${params.toString()}`);
  };

  // Handle Clear Filters
  const clearFilters = () => {
    router.push(`/all-products`); // Clear all query parameters
    setPriceRange([0, 500]); // Reset price range
    setDiscountRange([0, 100]); // Reset discount range
    setSortOption("price-asc"); // Reset sort option
  };

  return (
    <div className="flex flex-col gap-6 p-4">
      {/* Price Range Filter */}
      <div>
        <h4 className="text-lg font-medium">Filter by Price</h4>
        <Slider
          value={priceRange}
          onValueChange={(value) => setPriceRange(value)}
          min={0}
          max={10000}
          step={50}
        />
        <div className="flex justify-between text-sm">
          <span>₹{priceRange[0]}</span>
          <span>₹{priceRange[1]}</span>
        </div>
      </div>

      {/* Discount Range Filter */}
      <div>
        <h4 className="text-lg font-medium">Filter by Discount</h4>
        <Slider
          value={discountRange}
          onValueChange={(value) => setDiscountRange(value)}
          min={0}
          max={100}
          step={5}
        />
        <div className="flex justify-between text-sm">
          <span>{discountRange[0]}%</span>
          <span>{discountRange[1]}%</span>
        </div>
      </div>

      {/* Sort Options */}
      <div>
        <h4 className="text-lg font-medium">Sort by</h4>
        <Select onValueChange={setSortOption} defaultValue="price-asc">
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Sort Options" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="price-asc">Price: Low to High</SelectItem>
            <SelectItem value="price-desc">Price: High to Low</SelectItem>
            <SelectItem value="discount-asc">Discount: Low to High</SelectItem>
            <SelectItem value="discount-desc">Discount: High to Low</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Buttons */}
      <div className="flex gap-4">
        <Button onClick={applyFilters} className="flex-1 bg-primary">
          Apply Filters
        </Button>
        <Button onClick={clearFilters} variant="outline" className="flex-1">
          Clear Filters
        </Button>
      </div>
    </div>
  );
};

export default ProductFilters;
