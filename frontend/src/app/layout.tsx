import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "OfferHub - 开源面试备战平台",
    template: "%s | OfferHub",
  },
  description: "聚合全网面试题，AI智能陪练，帮你拿到心仪Offer。面经分享、题库解析、学习路径，开源免费。",
  keywords: ["面试题", "面经", "LeetCode", "Java面试", "前端面试", "后端面试", "算法", "OfferHub"],
  authors: [{ name: "OfferHub" }],
  openGraph: {
    type: "website",
    locale: "zh_CN",
    siteName: "OfferHub",
    title: "OfferHub - 开源面试备战平台",
    description: "聚合全网面试题，AI智能陪练，帮你拿到心仪Offer",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
