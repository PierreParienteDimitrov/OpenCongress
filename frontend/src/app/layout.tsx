import type { Metadata } from "next";
import { Suspense } from "react";
import {
  Geist,
  Geist_Mono,
  Source_Code_Pro,
  Domine,
} from "next/font/google";
import "./globals.css";
import QueryProvider from "@/components/providers/QueryProvider";
import { Navbar } from "@/components/nav/Navbar";
import { ChatInterface } from "@/components/chat/ChatInterface";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const sourceCodePro = Source_Code_Pro({
  variable: "--font-source-code-pro",
  subsets: ["latin"],
});

const domine = Domine({
  variable: "--font-domine",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "OpenCongress - Track Legislative Activity",
  description: "Track congressional votes, bills, and your representatives",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${sourceCodePro.variable} ${domine.variable} flex min-h-screen flex-col antialiased`}
      >
        <QueryProvider>
          <Navbar />
          <div className="flex-1">{children}</div>
          <Suspense>
            <ChatInterface />
          </Suspense>
        </QueryProvider>
      </body>
    </html>
  );
}
