import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GridFlow Control Room",
  description: "Race-day queue safety operations",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
