import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import StoreProvider from "@/provider/StoreProvider";
import { DarkModeButton } from "@/components/shared/DarkModeButton";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "ShopEase",
  description: "Convenient Shopping Everyday!!",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <StoreProvider>
          <div className="absolute top-4 right-4 z-50">
            <DarkModeButton />
          </div>

          {/* Main Content */}
          <div>{children}</div>
        </StoreProvider>
      </body>
    </html>
  );
}
