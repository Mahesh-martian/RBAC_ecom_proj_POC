import { LucideIcon } from "lucide-react";

export interface Vendor {
  id: string;
  name: string;
  email: string;
  profilePhoto?: string | null;
  isDeleted: boolean;
  isSuspended: boolean;
  createdAt: string;
  updatedAt: string;
  follows: object[];
  orders: object[];
  products: object[];
  shop?: object | null;
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  profilePhoto?: string | null;
  isDeleted: boolean;
  isSuspended: boolean;
  createdAt: string;
  updatedAt: string;
  cart: object[];
  follows: object[];
  orders: object[];
  reviews: object[];
  payments: object[];
}

export interface UserWithoutPassword {
  id: string;
  email: string;
  role: "ADMIN" | "VENDOR" | "CUSTOMER";
  name: string;
  vendor?: Vendor | null;
  customer?: Customer | null;
}

export interface BackendUser {
  accessToken: string;
  refreshToken: string;
  userWithoutPassword: UserWithoutPassword;
}

export interface AuthState {
  user: User | null;
}

export interface User {
  userId: string;
  email: string;
  role: "ADMIN" | "VENDOR" | "CUSTOMER";
  name: string;
  profilePhoto: string | null;
  vendorId: string;
  customerId: string;
}

export interface NavItem {
  label: string;
  component: React.ComponentType;
}

export type SidebarItems = {
  [role: string]: NavItem[];
};

export interface ShopApiResponse {
  data: {
    id: string;
    name: string;
    logo: string;
    description: string;
    createdAt: string;
    deletedAt: null | boolean;
    isBlackListed: boolean;
    updatedAt: string;
    vendorId: string;
  };
  message: string;
  success: boolean;
}

export interface ReviewData {
  reviewId: string;
  rating: number;
  comment: string;
}

// export interface ProductData {
//   productId: string;
//   productName: string;
//   productDescription: string;
//   productReviews?: ReviewData[];
//   categoryId: string; // Required
//   price: number; // Required
//   discount: number; // Required
//   image: string[]; // Required
//   inventory: number; // Required
// }

export interface VendorData {
  vendorId: string;
  vendorName: string;
  follows?: FollowData[];
}

export interface FollowData {
  followId: string;
  customerId: string;
}

export interface ShopData {
  shopId: string;
  name: string;
  description: string;
  logo: string;
  products?: ProductData[];
  vendor?: VendorData;
  isBlackListed?: boolean;
}

export interface ShopRouteShopData extends ShopData {
  productsQuantity: number;
  followers: number;
}

export interface AllShopsApiResponse {
  data: {
    id: string;
    name: string;
    logo: string;
    description: string;
    createdAt: string;
    deletedAt: null | boolean;
    isBlackListed: boolean;
    updatedAt: string;
    vendorId: string;
    products?: {
      id: string;
      name: string;
      description: string;
      reviews?: {
        id: string;
        rating: number;
        comment: string;
      }[];
    }[];
    vendor?: {
      id: string;
      name: string;
      follows?: {
        id: string;
        customerId: string;
      }[];
    };
  }[];
  message: string;
  success: boolean;
  meta: {
    page: number;
    limit: number;
    total: number;
  };
}

export interface ProductApiResponse {
  data: {
    categoryId: string;
    discount: number;
    image: string[];
    inventory: number;
    price: number;
    shopId: string;
    id: string;
    name: string;
    description: string;
    createdAt: string;
    deletedAt: null | boolean;
    updatedAt: string;
    vendorId: string;
  }[];
  message: string;
  success: boolean;
}
export interface SingleProductApiResponse {
  data: {
    id: string;
    name: string;
    description: string;
    categoryId: string;
    discount: number;
    image: string[];
    inventory: number;
    price: number;
    shopId: string;
    vendorId: string;
    createdAt: string;
    updatedAt: string;
    deletedAt: null | string;

    // Category data
    category: {
      id: string;
      name: string;
      description?: string;
    };

    // Shop data
    shop: {
      id: string;
      name: string;
      description?: string;
      logo?: string;
    };

    // Reviews data
    reviews: Array<{
      id: string;
      rating: number;
      comment?: string;
      createdAt: string;
      customer: {
        id: string;
        name: string;
        profilePhoto?: string;
      };
    }>;
  };
  message: string;
  success: boolean;
}

export interface VendorProductApiResponse {
  data: {
    categoryName: string;
    categoryId: string;
    discount: number;
    image: string[];
    inventory: number;
    price: number;
    shopId: string;
    id: string;
    name: string;
    description: string;
    createdAt: string;
    deletedAt: null | boolean;
    updatedAt: string;
    vendorId: string;
  }[];
  message: string;
  success: boolean;
  meta: {
    page: number;
    total: number;
    limit: number;
  };
}

export interface ProductData {
  shopId: string;
  productId: string;
  categoryId: string;
  vendorId: string;
  name: string;
  discount: number;
  description: string;
  image: string[];
  inventory: number;
  price: number;
}

export interface VendorProductData {
  categoryId: string;
  shopId: string;
  productId: string;
  categoryName: string;
  name: string;
  description: string;
  discount: number;
  inventory: number;
  price: number;
  image: string[];
}

export interface VendorProductActions extends VendorProductData {
  handleEdit: (product: VendorProductData) => void;
  handleDuplicate: (product: VendorProductData) => Promise<void>;
  handleFlashSale: (product: VendorProductData) => void;
}

export interface SingleProductData {
  productId: string;
  name: string;
  description: string;
  categoryId: string;
  discount: number;
  image: string[];
  inventory: number;
  price: number;
  shopId: string;
  vendorId: string;
  // Category information
  category?: {
    name: string;
    description?: string;
  };

  // Shop information
  shop?: {
    name: string;
    description?: string;
    logo?: string;
  };

  // Reviews information
  reviews?: Array<{
    id: string;
    rating: number;
    comment?: string;
    createdAt: string;
    customer: {
      id: string;
      name: string;
      profilePhoto?: string;
    };
  }>;
}

export interface EditProductRequest {
  productId: string;
  name: string;
  description: string;
  discount: number;
  inventory: number;
  price: number;
  additionalImages: File[];
}

export interface CreateShopRequest {
  name: string;
  description: string;
  file: File;
}

export interface DuplicationAlertProps {
  isAlertOpen: boolean;
  setIsAlertOpen: (open: boolean) => void;
  handleDuplicate: () => void;
  isLoading: boolean;
}

export interface FeatureCardProps {
  Icon: LucideIcon;
  text: string;
}

interface PaymentMethodOptions {
  card: {
    installments: any | null;
    mandate_options: any | null;
    network: string | null;
    request_three_d_secure: string;
  };
}

interface PaymentMetadata {
  id: string;
  object: string;
  amount: number;
  amount_capturable: number;
  amount_details: {
    tip?: Record<string, any>;
  };
  amount_received: number;
  application: string | null;
  application_fee_amount: number | null;
  automatic_payment_methods: any | null;
  canceled_at: number | null;
  cancellation_reason: string | null;
  capture_method: string;
  client_secret: string;
  confirmation_method: string;
  created: number;
  currency: string;
  customer: string | null;
  description: string | null;
  invoice: string | null;
  last_payment_error: any | null;
  latest_charge: string;
  livemode: boolean;
  metadata?: Record<string, any>;
  next_action: any | null;
  on_behalf_of: string | null;
  payment_method: string;
  payment_method_configuration_details: any | null;
  payment_method_options: PaymentMethodOptions;
  payment_method_types: string[];
  processing: any | null;
  receipt_email: string | null;
  review: any | null;
  setup_future_usage: any | null;
  shipping: any | null;
  source: any | null;
  statement_descriptor: string | null;
  statement_descriptor_suffix: string | null;
  status: string;
  transfer_data: any | null;
  transfer_group: string | null;
}

export interface PaymentResponse {
  data: PaymentMetadata;
  message: string;
  success: boolean;
  meta?: {
    total: number;
    page: number;
    limit: number;
  };
}

export interface Product {
  productId: string;
  quantity: number;
  price: number;
  discount: number;
}

export interface StructuredCartData {
  vendorId: string;
  totalAmount: number;
  products: Product[];
}

export interface OrderItem {
  id: string;
  orderId: string;
  productId: string;
  quantity: number;
  price: number;
  discount: number;
  createdAt: string;
  updatedAt: string;
}

export interface Order {
  id: string;
  customerId: string;
  vendorId: string;
  totalAmount: number;
  status: string;
  createdAt: string;
  updatedAt: string;
  deletedAt: string | null;
  order_items?: OrderItem[];
}

export interface OrderApiResponse {
  statusCode: number;
  success: boolean;
  message: string;
  data: Order[];
  meta: {
    page: number;
    total: number;
    limit: number;
  };
}
export interface CreateOrderApiResponse {
  statusCode: number;
  success: boolean;
  message: string;
  data: Order;
  meta?: {
    page: number;
    total: number;
    limit: number;
  };
}

export interface ProductInShopDetailPage {
  id: string;
  name: string;
  price: number;
  description: string;
  categoryId: string;
  inventory: number;
  image: string;
  vendorId: string;
  shopId: string;
  discount: number;
}

// Response type for the follow/unfollow actions
export interface FollowResponse {
  success: boolean;
  message: string;
  data: {
    id: string;
    vendorId: string;
    customerId: string;
    isDeleted: boolean;
    createdAt: string;
  };
}

export interface ErrorData {
  success: boolean;
  message: string;
  error?: {
    statusCode: number;
  };
}
// Error type
export interface FollowError {
  data: ErrorData;
}

export interface FollowerCountResponse {
  success: boolean;
  message: string;
  data: {
    data: number; // Represents the actual follower count
  };
}
