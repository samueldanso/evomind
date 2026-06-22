import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Evo",
  description: "Agent-first learning platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <nav className="flex items-center justify-between border-b px-6 py-3">
          <Link href="/" className="text-sm font-bold">
            Evo
          </Link>
          <div className="flex gap-4 text-sm">
            <Link href="/kb" className="text-muted-foreground hover:text-foreground transition-colors">
              KB
            </Link>
            <Link href="/chat" className="text-muted-foreground hover:text-foreground transition-colors">
              Chat
            </Link>
            <Link href="/runs" className="text-muted-foreground hover:text-foreground transition-colors">
              Runs
            </Link>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
