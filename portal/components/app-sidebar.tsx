"use client";

import type { Icon as PhosphorIcon } from "@phosphor-icons/react";
import {
  Books,
  GithubLogo,
  Info,
  List,
  MagnifyingGlass,
  Monitor,
  Moon,
  PlusCircle,
  SidebarSimple,
  Sun,
  X,
} from "@phosphor-icons/react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { AddSourceDialog } from "./add-source-dialog";
import { useSidebar } from "./sidebar-context";

const NAV_ITEMS: { href: string; label: string; icon: PhosphorIcon }[] = [
  { href: "/search", label: "Search", icon: MagnifyingGlass },
  { href: "/wiki", label: "Wiki", icon: Books },
  { href: "/docs", label: "Docs", icon: Info },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const { collapsed, setCollapsed } = useSidebar();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sourceDialogOpen, setSourceDialogOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  // ESC to close dialog
  useEffect(() => {
    function handleKeydown(e: KeyboardEvent) {
      if (e.key === "Escape" && sourceDialogOpen) {
        setSourceDialogOpen(false);
      }
    }
    document.addEventListener("keydown", handleKeydown);
    return () => document.removeEventListener("keydown", handleKeydown);
  }, [sourceDialogOpen]);

  function cycleTheme() {
    if (theme === "dark") setTheme("light");
    else if (theme === "light") setTheme("system");
    else setTheme("dark");
  }

  const ThemeIcon = !mounted
    ? Monitor
    : theme === "dark"
      ? Moon
      : theme === "light"
        ? Sun
        : Monitor;

  return (
    <>
      {/* Mobile trigger */}
      <button
        type="button"
        onClick={() => setMobileOpen(true)}
        className="fixed top-4 left-4 z-40 lg:hidden p-2 rounded-xl transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]"
        style={{
          background: "var(--surface-3)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          border: "1px solid var(--border-default)",
        }}
        aria-label="Open menu"
      >
        <List size={18} weight="bold" style={{ color: "var(--ink-muted)" }} />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <button
          type="button"
          className="fixed inset-0 z-40 lg:hidden cursor-default"
          onClick={() => setMobileOpen(false)}
          onKeyDown={(e) => e.key === "Escape" && setMobileOpen(false)}
          style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }}
          aria-label="Close menu"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-dvh flex flex-col border-r transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        } ${collapsed ? "w-[60px]" : "w-[240px]"}`}
        style={{
          background: "var(--surface-0)",
          borderColor: "var(--border-subtle)",
        }}
      >
        {/* Header */}
        <div
          className={`flex items-center h-14 flex-shrink-0 ${collapsed ? "justify-center px-2" : "justify-between px-4"}`}
        >
          <Link
            href="/"
            className="flex items-center gap-2.5 transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:opacity-80"
            onClick={() => setMobileOpen(false)}
          >
            <Image
              src="/logo.svg"
              alt="EvoMind"
              width={20}
              height={20}
              className="rounded-md flex-shrink-0"
            />
            {!collapsed && (
              <span
                className="text-xs font-medium tracking-[0.15em] uppercase"
                style={{ color: "var(--ink-muted)" }}
              >
                EvoMind
              </span>
            )}
          </Link>

          {/* Mobile close / Desktop collapse */}
          {!collapsed && (
            <>
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                className="lg:hidden p-1.5 rounded-lg transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]"
                style={{ color: "var(--ink-muted)" }}
                aria-label="Close menu"
              >
                <X size={16} weight="bold" />
              </button>
              <button
                type="button"
                onClick={() => setCollapsed(true)}
                className="hidden lg:flex p-1.5 rounded-lg transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:bg-[var(--surface-2)]"
                style={{ color: "var(--ink-muted)" }}
                aria-label="Collapse sidebar"
                title="Collapse (⌘B)"
              >
                <SidebarSimple size={16} weight="bold" />
              </button>
            </>
          )}
          {collapsed && (
            <button
              type="button"
              onClick={() => setCollapsed(false)}
              className="hidden lg:flex absolute top-4 left-1/2 -translate-x-1/2 p-1.5 rounded-lg transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:bg-[var(--surface-2)]"
              style={{ color: "var(--ink-muted)" }}
              aria-label="Expand sidebar"
              title="Expand (⌘B)"
            >
              <SidebarSimple size={16} weight="bold" className="rotate-180" />
            </button>
          )}
        </div>

        {/* Nav */}
        <nav className={`flex-1 py-2 space-y-0.5 overflow-y-auto ${collapsed ? "px-1.5" : "px-3"}`}>
          {/* Add Source button */}
          <button
            type="button"
            onClick={() => {
              setSourceDialogOpen(true);
              setMobileOpen(false);
            }}
            className={`w-full flex items-center gap-2.5 py-2 rounded-lg text-sm font-medium transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] border border-transparent hover:bg-[var(--accent-warm-faint)] ${
              collapsed ? "justify-center px-0" : "px-3"
            }`}
            style={{ color: "var(--accent-warm)" }}
            title={collapsed ? "Add source" : undefined}
          >
            <PlusCircle size={18} weight="bold" className="flex-shrink-0" />
            {!collapsed && <span>Add source</span>}
          </button>

          {/* Nav links */}
          {NAV_ITEMS.map((item) => (
            <SidebarLink
              key={item.href}
              href={item.href}
              icon={item.icon}
              label={item.label}
              active={pathname === item.href || pathname.startsWith(`${item.href}/`)}
              collapsed={collapsed}
              onClick={() => setMobileOpen(false)}
            />
          ))}
        </nav>

        {/* Footer */}
        <div
          className={`py-3 border-t flex-shrink-0 space-y-0.5 ${collapsed ? "px-1.5" : "px-3"}`}
          style={{ borderColor: "var(--border-subtle)" }}
        >
          {/* Theme toggle */}
          <button
            type="button"
            onClick={cycleTheme}
            className={`w-full flex items-center gap-2.5 py-2 rounded-lg text-sm transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:bg-[var(--surface-2)] ${
              collapsed ? "justify-center px-0" : "px-3"
            }`}
            style={{ color: "var(--ink-muted)" }}
            title={collapsed ? `Theme: ${theme}` : undefined}
          >
            <ThemeIcon size={18} weight="bold" className="flex-shrink-0" />
            {!collapsed && (
              <span>
                {!mounted
                  ? "Theme"
                  : theme === "dark"
                    ? "Dark"
                    : theme === "light"
                      ? "Light"
                      : "System"}
              </span>
            )}
          </button>

          {/* GitHub */}
          <a
            href="https://github.com/samueldanso/evomind"
            target="_blank"
            rel="noopener noreferrer"
            className={`flex items-center gap-2.5 py-2 rounded-lg text-sm transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:bg-[var(--surface-2)] ${
              collapsed ? "justify-center px-0" : "px-3"
            }`}
            style={{ color: "var(--ink-muted)" }}
            title={collapsed ? "GitHub" : undefined}
          >
            <GithubLogo size={18} weight="bold" className="flex-shrink-0" />
            {!collapsed && (
              <>
                <span>GitHub</span>
                <svg
                  width={11}
                  height={11}
                  viewBox="0 0 12 12"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={1.5}
                  className="opacity-50 ml-auto"
                  aria-hidden="true"
                >
                  <path d="M3.5 1.5h7v7M10.5 1.5L1.5 10.5" />
                </svg>
              </>
            )}
          </a>
        </div>
      </aside>

      {/* Add Source Dialog */}
      <AddSourceDialog open={sourceDialogOpen} onClose={() => setSourceDialogOpen(false)} />
    </>
  );
}

function SidebarLink({
  href,
  icon: Icon,
  label,
  active,
  collapsed,
  onClick,
}: {
  href: string;
  icon: PhosphorIcon;
  label: string;
  active: boolean;
  collapsed: boolean;
  onClick?: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className={`relative flex items-center gap-2.5 py-2 rounded-lg text-sm font-medium transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] ${
        collapsed ? "justify-center px-0" : "px-3"
      } ${
        active
          ? "bg-[var(--surface-2)] border border-[var(--border-strong)]"
          : "hover:bg-[var(--surface-2)] border border-transparent"
      }`}
      style={{ color: active ? "var(--ink)" : "var(--ink-muted)" }}
      title={collapsed ? label : undefined}
    >
      {active && !collapsed && (
        <span
          className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-4 rounded-full"
          style={{ background: "var(--accent-warm)" }}
        />
      )}
      <Icon size={18} weight={active ? "fill" : "bold"} className="flex-shrink-0" />
      {!collapsed && <span>{label}</span>}
    </Link>
  );
}
