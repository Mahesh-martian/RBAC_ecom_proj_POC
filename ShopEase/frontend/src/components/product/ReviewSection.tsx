import { SingleProductData } from "@/types";
import React from "react";

import ReviewSubmitForm from "../forms/ReviewSubmitForm";

interface ReviewInfoProps {
  product: SingleProductData;
  renderStars: (rating: number) => JSX.Element[];
}

const ReviewSection: React.FC<ReviewInfoProps> = ({ product, renderStars }) => {
  return (
    <div className="mt-16">
      <h2 className="text-2xl font-bold mb-8">Reviews</h2>
      <div className="space-y-8">
        {product.reviews?.map((review) => (
          <div key={review.id} className="border-b pb-8">
            <div className="flex items-center gap-4 mb-2">
              <span className="font-semibold">{review.customer.name}</span>
              <span className="text-sm text-muted-foreground">
                {new Date(review.createdAt).toLocaleDateString()}
              </span>
            </div>
            <div className="flex mb-2">{renderStars(review.rating)}</div>
            <p className="text-muted-foreground">{review.comment}</p>
          </div>
        )) || <p>No reviews available.</p>}
      </div>

      {/* Add Review Form */}
      <ReviewSubmitForm productId={product.productId} />
    </div>
  );
};

export default ReviewSection;
