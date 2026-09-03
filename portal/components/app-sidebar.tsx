"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  House,
  Books,
  PlusCircle,
  MagnifyingGlass,
  Info,
  GithubLogo,
  List,
  X,
} from "@phosphor-icons/react";

import type { Icon as PhosphorIcon } from "@phosphor-icons/react";

const NAV_ITEMS: { href: string; label: string; icon: PhosphorIcon }[] = [
  { href: "/wiki", label: "Wiki", icon: Books },
  { href: "/ingest", label: "Add source", icon: PlusCircle },
  { href: "/search", label: "Search", icon: MagnifyingGlass },
  { href: "/docs", label: "Docs", icon: Info },
];

export function AppSidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Mobile trigger */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed top-4 left-4 z-40 lg:hidden p-2 rounded-xl transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]"
        style={{
          background: "rgba(24,24,24,0.75)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          border: "1px solid rgba(255,255,255,0.08)",
        }}
        aria-label="Open menu"
      >
        <List size={18} weight="bold" style={{ color: "rgba(245,245,244,0.6)" }} />
      </button>

      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          onClick={() => setOpen(false)}
          onKeyDown={(e) => e.key === "Escape" && setOpen(false)}
          style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-dvh w-[240px] flex flex-col border-r border-[rgba(255,255,255,0.04)] bg-black transition-transform duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between h-14 px-4 flex-shrink-0">
          <Link
            href="/"
            className="flex items-center gap-2.5 transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:opacity-80"
            onClick={() => setOpen(false)}
          >
            <Image src="/logo.svg" alt="EvoMind" width={20} height={20} className="rounded-md" />
            <span className="text-xs font-medium tracking-[0.15em] uppercase text-[rgba(245,245,244,0.5)]">
              EvoMind
            </span>
          </Link>

          {/* Mobile close */}
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="lg:hidden p-1.5 rounded-lg text-[rgba(245,245,244,0.4)] hover:text-[#f5f5f4] hover:bg-[rgba(255,255,255,0.06)] transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]"
            aria-label="Close menu"
          >
            <X size={16} weight="bold" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-2 space-y-0.5 overflow-y-auto">
          <SidebarLink
            href="/"
            icon={House}
            label="Home"
            active={pathname === "/"}
            onClick={() => setOpen(false)}
          />

          {NAV_ITEMS.map((item) => (
            <SidebarLink
              key={item.href}
              href={item.href}
              icon={item.icon}
              label={item.label}
              active={pathname === item.href || pathname.startsWith(`${item.href}/`)}
              onClick={() => setOpen(false)}
            />
          ))}
        </nav>

        {/* Footer */}
        <div className="px-3 py-3 border-t border-[rgba(255,255,255,0.04)] flex-shrink-0">
          <a
            href="https://github.com/samueldanso/evomind"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-[rgba(245,245,244,0.4)] hover:text-[rgba(245,245,244,0.7)] hover:bg-[rgba(255,255,255,0.04)] transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]"
          >
            <GithubLogo size={18} weight="bold" />
            <span>GitHub</span>
            <svg width={11} height={11} viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth={1.5} className="opacity-50 ml-auto">
              <path d="M3.5 1.5h7v7M10.5 1.5L1.5 10.5" />
            </svg>
          </a>
        </div>
      </aside>
    </>
  );
}

function SidebarLink({
  href,
  icon: Icon,
  label,
  active,
  onClick,
}: {
  href: string;
  icon: PhosphorIcon;
  label: string;
  active: boolean;
  onClick?: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className={`relative flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] ${
        active
          ? "bg-[rgba(255,255,255,0.06)] text-[#f5f5f4] border border-[rgba(255,255,255,0.1)]"
          : "text-[rgba(245,245,244,0.45)] hover:text-[rgba(245,245,244,0.8)] hover:bg-[rgba(255,255,255,0.03)] border border-transparent"
      }`}
    >
      {active && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-4 rounded-full bg-[#d4a574]" />
      )}
      <Icon size={18} weight={active ? "fill" : "bold"} className="flex-shrink-0" />
      <span>{label}</span>
    </Link>
  );
}
