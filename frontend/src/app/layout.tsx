import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/lib/query-client";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "Catalogue IQ — Multimodal Product Discovery",
  description:
    "AI-powered product search across text, image, and multimodal inputs with rich attribute extraction.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <Navbar />
          <main className="min-h-[calc(100vh-4rem)]">{children}</main>
        </QueryProvider>
      </body>
    </html>
  );
}
