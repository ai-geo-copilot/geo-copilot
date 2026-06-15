import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GEO Copilot",
  description: "Single-URL GEO analysis copilot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
