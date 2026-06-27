import Category from "@/components/dashboard/admin/Category";
import Transactions from "@/components/dashboard/admin/Transactions";
import User from "@/components/dashboard/admin/User";
import AdminShops from "@/components/dashboard/admin/AdminShops";
import VendorOrders from "@/components/dashboard/vendor/VendorOrders";
import VendorProducts from "@/components/dashboard/vendor/VendorProducts";
import VendorReviews from "@/components/dashboard/vendor/VendorReviews";
import VendorShop from "@/components/dashboard/vendor/VendorShop";
import VendorFlashSale from "@/components/dashboard/vendor/VendorFlashSale";
import Cart from "@/components/dashboard/customer/Cart";
import CustomerOrders from "@/components/dashboard/customer/CustomerOrders";
import RecentProducts from "@/components/dashboard/customer/RecentProducts";
import { SidebarItems } from "@/types";
import { Truck, Package, Shield } from "lucide-react";
import ChangePassword from "@/components/dashboard/ChangePassword";

export const allowedRoles = {
  admin: ["ADMIN"],
  vendor: ["VENDOR"],
  customer: ["CUSTOMER"],
};

export const sidebarItems: SidebarItems = {
  VENDOR: [
    { label: "Shop", component: VendorShop },
    { label: "Products", component: VendorProducts },
    { label: "Orders", component: VendorOrders },
    { label: "Review", component: VendorReviews },
    { label: "Flash Sale", component: VendorFlashSale },
    { label: "Change Password", component: ChangePassword },
  ],
  CUSTOMER: [
    { label: "Orders", component: CustomerOrders },
    { label: "Recent Products", component: RecentProducts },
    { label: "Cart", component: Cart },

    { label: "Change Password", component: ChangePassword },
  ],
  ADMIN: [
    { label: "Users", component: User },
    { label: "Category", component: Category },
    { label: "Shops", component: AdminShops },
    // { label: "Orders", component: AdminOrders },
    { label: "Transactions", component: Transactions },
    { label: "Change Password", component: ChangePassword },
  ],
};

export const selectButtonCategories = [
  { id: "5f2afe7a-58d4-442f-9e2f-f430f69c3583", name: "Electronics", count: 9, icon: "🔊" },
  { id: "6c69c238-926f-4e75-87a5-73824d335fc8", name: "Fashion", count: 15, icon: "👗" },
  { id: "d277e6cc-06a0-4b9b-9c4e-3d2f8d362f8b", name: "Home & Kitchen", count: 20, icon: "🪑" },
  { id: "4392db03-5479-42f9-900f-8aefd70a04fd", name: "Beauty & Personal Care", count: 12, icon: "💄" },
  { id: "dfe36168-781f-4c77-a6f2-224199b3bfb6", name: "Sports & Outdoors", count: 8, icon: "⚽" }
];


export const cardCategories = [
  { id: 1, title: "Driftwood Table Decor", count: 20, icon: "🪑" },
  { id: 2, title: "Floor Driftwood Sculpture", count: 12, icon: "🎨" },
  { id: 3, title: "Tree", count: 3, icon: "🎄" },
  { id: 4, title: "Wooden Bluetooth Speaker", count: 9, icon: "🔊" },
  { id: 5, title: "Receivers Amplifiers", count: 10, icon: "🕯️" },
  { id: 6, title: "Appetizer Plate Set", count: 5, icon: "🍽️" },
];

export const carouselItems = [
  {
    bgClass: "bg-stone-600",
    h3Text: "Stationary",
    spanText: "30% off",
    h2Text: "on All Pen",
    imageSrc: "/images/pen.jpg",
  },
  {
    bgClass: "bg-blue-600",
    h3Text: "Notebooks",
    spanText: "20% off",
    h2Text: "on Premium Notebooks",
    imageSrc: "/images/sleeper.jpg",
  },
  {
    bgClass: "bg-green-600",
    h3Text: "Art Supplies",
    spanText: "40% off",
    h2Text: "on All Sketchbooks",
    imageSrc: "/images/shoe.jpg",
  },
];

export const features = [
  {
    Icon: Truck,
    text: "Free Shipping on orders over $100",
  },
  {
    Icon: Package,
    text: "1 Day Returns if you change your mind",
  },
  {
    Icon: Shield,
    text: "Guaranteed 100% Organic from natural farms",
  },
];

export const randomColors = ["blue", "pink", "red", "purple", "green"];
export const randomTags = [
  "fashion",
  "sale",
  "new arrival",
  "limited edition",
  "exclusive",
];
