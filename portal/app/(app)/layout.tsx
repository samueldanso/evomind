import { AppSidebar } from "@/components/app-sidebar";

export default function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="flex min-h-dvh">
      <AppSidebar />

      {/* Main content — offset by sidebar width on desktop */}
      <main className="flex-1 lg:ml-[240px] min-w-0">
        {children}
      </main>
    </div>
  );
}
