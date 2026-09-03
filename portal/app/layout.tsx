import type { Metadata, Viewport } from "next";
import Image from "next/image";
import Link from "next/link";
import { Inter, Instrument_Serif, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

const instrumentSerif = Instrument_Serif({
  weight: "400",
  subsets: ["latin"],
  display: "swap",
  variable: "--font-serif",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "EvoMind — AI-Powered Knowledge Base",
  description:
    "Personal knowledge base with hybrid RAG retrieval, autonomous research agents, and a compounding knowledge graph.",
  icons: {
    icon: "/favicon.svg",
  },
};

export const viewport: Viewport = {
  themeColor: "#09090b",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${instrumentSerif.variable} ${jetbrainsMono.variable}`}
    >
      <body className="min-h-screen bg-[#09090b] text-[#f5f5f4] antialiased">
        <header
          className="sticky top-0 z-30 h-[52px] flex items-center px-5"
          style={{
            background: "rgba(9,9,11,0.88)",
            backdropFilter: "blur(16px)",
            WebkitBackdropFilter: "blur(16px)",
            borderBottom: "1px solid rgba(255,255,255,0.04)",
          }}
        >
          <div className="flex items-center gap-2">
            <Link href="/" className="flex items-center gap-2.5 hover:opacity-70 transition-opacity">
              <Image src="/logo.svg" alt="EvoMind" width={24} height={24} className="rounded-md" />
              <span className="hidden sm:inline text-[11px] font-medium tracking-[0.2em] uppercase text-[rgba(245,245,244,0.45)]">
                EvoMind
              </span>
            </Link>
          </div>

          <nav className="flex-1 flex items-center justify-center gap-1">
            <NavLink href="/wiki">Wiki</NavLink>
            <NavLink href="/search">Search</NavLink>
          </nav>

          <div className="flex items-center">
            <a
              href="https://github.com/samueldanso/evomind"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg text-[rgba(245,245,244,0.4)] hover:text-[#f5f5f4] hover:bg-[rgba(255,255,255,0.04)] transition-all"
              aria-label="View on GitHub"
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
              </svg>
            </a>
          </div>
        </header>

        <main className="min-h-[calc(100vh-52px)]">{children}</main>
      </body>
    </html>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="px-3 py-1.5 rounded-lg text-[13px] font-medium text-[rgba(245,245,244,0.42)] hover:text-[#f5f5f4] hover:bg-[rgba(255,255,255,0.04)] transition-all"
    >
      {children}
    </Link>
  );
}
