import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GEO Copilot — AI 搜索优化诊断",
  description: "输入任意网址，基于页面证据和GEO前沿方法知识库，获得结构化优化反馈报告",
  openGraph: {
    title: "GEO Copilot — AI 搜索优化诊断",
    description: "输入任意网址，基于页面证据和GEO前沿方法知识库，获得结构化优化反馈报告",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
