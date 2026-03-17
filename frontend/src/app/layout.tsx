import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OfferHub - 开源面试备战平台",
  description: "聚合全网面试题，AI智能陪练，帮你拿到心仪Offer",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
