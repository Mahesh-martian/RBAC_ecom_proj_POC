import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: "standalone",
  images: {
    // Allow remote product images (Flipkart/rukminim CDN, Unsplash, Cloudinary, etc.).
    // `unoptimized` lets the browser load source URLs directly, which avoids the Next
    // image optimizer getting 403s from hotlink-protected CDNs like flixcart.
    unoptimized: true,
    remotePatterns: [
      { protocol: "https", hostname: "**" },
      { protocol: "http", hostname: "**" },
    ],
  },
};

export default nextConfig;
