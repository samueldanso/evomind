import Image from "next/image";
import Link from "next/link";

export default function MarketingLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <>
      {/* Floating island navbar */}
      <header className="fixed top-0 left-0 right-0 z-30 flex justify-center pt-4 px-4 pointer-events-none">
        <nav
          className="pointer-events-auto flex items-center gap-1 h-11 px-2 rounded-full"
          style={{
            background: "var(--surface-3)",
            backdropFilter: "blur(20px)",
            WebkitBackdropFilter: "blur(20px)",
            border: "1px solid var(--border-default)",
            boxShadow: "0 4px 24px rgba(0,0,0,0.15), 0 0 0 1px var(--border-subtle) inset",
          }}
        >
          <Link
            href="/"
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-full transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:bg-[var(--surface-2)]"
          >
            <Image src="/logo.svg" alt="EvoMind" width={20} height={20} className="rounded-md" />
            <span className="hidden sm:inline text-xs font-medium tracking-[0.15em] uppercase text-[var(--ink-muted)]">
              EvoMind
            </span>
          </Link>

          <div className="w-px h-4 bg-[var(--border-default)]" />

          <NavLink href="/wiki">Wiki</NavLink>
          <NavLink href="/search">Search</NavLink>
          <NavLink href="/docs">Docs</NavLink>
        </nav>
      </header>

      <main>{children}</main>

      {/* Footer */}
      <footer className="border-t border-[rgba(255,255,255,0.04)]">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <div className="grid grid-cols-1 sm:grid-cols-12 gap-12 sm:gap-8">
            <div className="sm:col-span-5">
              <div className="flex items-center gap-2.5 mb-4">
                <Image
                  src="/logo.svg"
                  alt="EvoMind"
                  width={20}
                  height={20}
                  className="rounded-md"
                />
                <span className="text-xs font-medium tracking-[0.15em] uppercase text-[var(--ink-secondary)]">
                  EvoMind
                </span>
              </div>
              <p className="text-sm leading-relaxed max-w-xs" style={{ color: "var(--ink-muted)" }}>
                Your personal AI knowledge base. Ingest, embed, and retrieve your knowledge with hybrid
                RAG.
              </p>
            </div>
            <div className="sm:col-span-3">
              <h4
                className="text-xs font-medium uppercase tracking-wider mb-4"
                style={{ color: "var(--ink-muted)" }}
              >
                Product
              </h4>
              <nav className="flex flex-col gap-2.5">
                <FooterLink href="/wiki">Wiki</FooterLink>
                <FooterLink href="/search">Search</FooterLink>
              </nav>
            </div>
            <div className="sm:col-span-4">
              <h4
                className="text-xs font-medium uppercase tracking-wider mb-4"
                style={{ color: "var(--ink-muted)" }}
              >
                Resources
              </h4>
              <nav className="flex flex-col gap-2.5">
                <FooterLink href="/docs">Docs</FooterLink>
                <FooterLink href="https://github.com/samueldanso/evomind" external>
                  GitHub
                </FooterLink>
              </nav>
            </div>
          </div>
        </div>
        <div className="border-t border-[rgba(255,255,255,0.04)]">
          <div className="mx-auto max-w-6xl px-6 py-5 flex items-center justify-center">
            <span className="text-xs" style={{ color: "var(--ink-faint)" }}>
              &copy; {new Date().getFullYear()} EvoMind. Your knowledge. Your control.
            </span>
          </div>
        </div>
      </footer>
    </>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="px-3 py-1.5 rounded-full text-sm font-medium text-[var(--ink-muted)] hover:text-[var(--ink)] hover:bg-[var(--surface-2)] transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]"
    >
      {children}
    </Link>
  );
}

function FooterLink({
  href,
  external,
  children,
}: {
  href: string;
  external?: boolean;
  children: React.ReactNode;
}) {
  if (external) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:text-[var(--ink)] inline-flex items-center gap-1"
        style={{ color: "var(--ink-tertiary)" }}
      >
        {children}
        <svg
          width={11}
          height={11}
          viewBox="0 0 12 12"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          className="opacity-50"
          aria-hidden="true"
        >
          <path d="M3.5 1.5h7v7M10.5 1.5L1.5 10.5" />
        </svg>
      </a>
    );
  }

  return (
    <Link
      href={href}
      className="text-sm transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:text-[var(--ink)]"
      style={{ color: "var(--ink-tertiary)" }}
    >
      {children}
    </Link>
  );
}
