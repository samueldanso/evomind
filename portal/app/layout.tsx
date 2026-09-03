import type { Metadata, Viewport } from "next";
import Image from "next/image";
import Link from "next/link";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";

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
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="min-h-screen bg-black text-[#f5f5f4] antialiased">
        {/* Floating island navbar */}
        <header className="fixed top-0 left-0 right-0 z-30 flex justify-center pt-4 px-4 pointer-events-none">
          <nav
            className="pointer-events-auto flex items-center gap-1 h-11 px-2 rounded-full"
            style={{
              background: "rgba(24,24,24,0.75)",
              backdropFilter: "blur(20px)",
              WebkitBackdropFilter: "blur(20px)",
              border: "1px solid rgba(255,255,255,0.08)",
              boxShadow: "0 4px 24px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.03) inset",
            }}
          >
            <Link
              href="/"
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-full transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:bg-[rgba(255,255,255,0.06)]"
            >
              <Image src="/logo.svg" alt="EvoMind" width={20} height={20} className="rounded-md" />
              <span className="hidden sm:inline text-xs font-medium tracking-[0.15em] uppercase text-[rgba(245,245,244,0.45)]">
                Evo
              </span>
            </Link>

            <div className="w-px h-4 bg-[rgba(255,255,255,0.08)]" />

            <NavLink href="/wiki">Wiki</NavLink>
            <NavLink href="/search">Search</NavLink>

            <div className="w-px h-4 bg-[rgba(255,255,255,0.08)]" />

            <a
              href="https://github.com/samueldanso/evomind"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-full text-[rgba(245,245,244,0.4)] hover:text-[#f5f5f4] hover:bg-[rgba(255,255,255,0.06)] transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]"
              aria-label="View on GitHub"
            >
              <svg width={14} height={14} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
              </svg>
            </a>
          </nav>
        </header>

        <main>{children}</main>

        {/* Footer */}
        <footer className="border-t border-[rgba(255,255,255,0.04)]">
          <div className="mx-auto max-w-6xl px-6 py-16">
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-12 sm:gap-8">
              {/* Brand */}
              <div className="sm:col-span-5">
                <div className="flex items-center gap-2.5 mb-4">
                  <Image src="/logo.svg" alt="EvoMind" width={20} height={20} className="rounded-md" />
                  <span className="text-xs font-medium tracking-[0.15em] uppercase text-[rgba(245,245,244,0.7)]">
                    EvoMind
                  </span>
                </div>
                <p className="text-sm leading-relaxed max-w-xs" style={{ color: "rgba(245,245,244,0.4)" }}>
                  Your personal research agent. Ingest, embed, and retrieve your knowledge with hybrid RAG.
                </p>
              </div>

              {/* Product links */}
              <div className="sm:col-span-3">
                <h4 className="text-xs font-medium uppercase tracking-wider mb-4" style={{ color: "rgba(245,245,244,0.35)" }}>
                  Product
                </h4>
                <nav className="flex flex-col gap-2.5">
                  <FooterLink href="/wiki">Wiki</FooterLink>
                  <FooterLink href="/search">Search</FooterLink>
                </nav>
              </div>

              {/* Resources */}
              <div className="sm:col-span-4">
                <h4 className="text-xs font-medium uppercase tracking-wider mb-4" style={{ color: "rgba(245,245,244,0.35)" }}>
                  Resources
                </h4>
                <nav className="flex flex-col gap-2.5">
                  <FooterLink href="https://github.com/samueldanso/evomind#readme" external>
                    Documentation
                  </FooterLink>
                  <FooterLink href="https://github.com/samueldanso/evomind" external>
                    GitHub
                  </FooterLink>
                </nav>
              </div>
            </div>
          </div>

          {/* Bottom bar */}
          <div className="border-t border-[rgba(255,255,255,0.04)]">
            <div className="mx-auto max-w-6xl px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-3">
              <span className="text-xs" style={{ color: "rgba(245,245,244,0.25)" }}>
                Built with SQLite + hybrid RAG
              </span>
              <span className="text-xs" style={{ color: "rgba(245,245,244,0.25)" }}>
                &copy; {new Date().getFullYear()} EvoMind. Your knowledge. Your control.
              </span>
              <a
                href="https://github.com/samueldanso/evomind/blob/main/LICENSE"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:text-[rgba(245,245,244,0.5)]"
                style={{ color: "rgba(245,245,244,0.25)" }}
              >
                MIT License
              </a>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="px-3 py-1.5 rounded-full text-sm font-medium text-[rgba(245,245,244,0.45)] hover:text-[#f5f5f4] hover:bg-[rgba(255,255,255,0.06)] transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]"
    >
      {children}
    </Link>
  );
}

function FooterLink({
  href,
  external,
  children,
}: { href: string; external?: boolean; children: React.ReactNode }) {
  if (external) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:text-[#f5f5f4] inline-flex items-center gap-1"
        style={{ color: "rgba(245,245,244,0.5)" }}
      >
        {children}
        <svg width={11} height={11} viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth={1.5} className="opacity-50">
          <path d="M3.5 1.5h7v7M10.5 1.5L1.5 10.5" />
        </svg>
      </a>
    );
  }

  return (
    <Link
      href={href}
      className="text-sm transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:text-[#f5f5f4]"
      style={{ color: "rgba(245,245,244,0.5)" }}
    >
      {children}
    </Link>
  );
}
