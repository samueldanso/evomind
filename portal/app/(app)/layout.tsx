"use client";

import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider, useSidebar } from "@/components/sidebar-context";

function AppContent({ children }: { children: React.ReactNode }) {
  const { collapsed } = useSidebar();

  return (
    <div className="flex min-h-dvh">
      <AppSidebar />
      <main
        className="flex-1 min-w-0 transition-[margin] duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] max-lg:ml-0"
        style={{ marginLeft: undefined }}
      >
        {/* Desktop-only left margin offset matching sidebar width */}
        <style>{`
          @media (min-width: 1024px) {
            main { margin-left: ${collapsed ? 60 : 240}px !important; }
          }
        `}</style>
        {children}
      </main>
    </div>
  );
}

export default function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <SidebarProvider>
      <AppContent>{children}</AppContent>
    </SidebarProvider>
  );
}
