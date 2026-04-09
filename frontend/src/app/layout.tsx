import type { Metadata } from "next";
import Script from "next/script";

import "../index.css";
import Header from "@/components/header";
import Footer from "@/components/footer";
import Providers from "@/components/providers";
import { LenisProvider } from "@/components/lenis-provider";

export const metadata: Metadata = {
  title: "Diagnostic System - Staging Area",
  description:
    "A diagnostic-first system that evaluates data readiness, structural integrity, and modeling risk before you commit to any ML pipeline.",
  keywords: [
    "machine learning",
    "data quality",
    "diagnostics",
    "data validation",
    "ML pipeline",
    "data readiness",
  ],
  authors: [{ name: "Diagnostic Sys" }],
  openGraph: {
    title: "Diagnostic System - Staging Area",
    description:
      "Diagnostics First. Modeling Second. Meticulous tools for high-stakes ML execution.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
        {process.env.NODE_ENV === "development" && (
          <Script
            src="//unpkg.com/react-grab/dist/index.global.js"
            crossOrigin="anonymous"
            strategy="beforeInteractive"
          />
        )}
      </head>
      <body className="flex flex-col min-h-screen" suppressHydrationWarning>
        <Providers>
          <LenisProvider>
            <Header />
            <div className="flex-grow">{children}</div>
            <Footer />
          </LenisProvider>
        </Providers>
      </body>
    </html>
  );
}
