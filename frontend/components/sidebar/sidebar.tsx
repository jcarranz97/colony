"use client";
import { useSidebar } from "@/components/layout/layout-context";
import { SidebarItem } from "./sidebar-item";
import {
  MdDashboard,
  MdCreditCard,
  MdListAlt,
  MdSettings,
} from "react-icons/md";

const NAV_ITEMS = [
  { href: "/cycles", label: "Cycles", icon: <MdDashboard /> },
  {
    href: "/payment-methods",
    label: "Payment Methods",
    icon: <MdCreditCard />,
  },
  { href: "/expense-templates", label: "Templates", icon: <MdListAlt /> },
  { href: "/settings", label: "Settings", icon: <MdSettings /> },
];

export function Sidebar() {
  const { collapsed } = useSidebar();

  return (
    <aside
      className={`flex flex-col h-full border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 transition-all duration-200 ${
        collapsed ? "w-16" : "w-60"
      }`}
    >
      <div className="flex items-center gap-2 px-4 h-16 border-b border-gray-200 dark:border-gray-800 flex-shrink-0">
        {!collapsed && (
          <span className="text-lg font-bold tracking-tight">Colony</span>
        )}
        {collapsed && <span className="text-lg font-bold">C</span>}
      </div>
      <nav className="flex flex-col gap-1 p-3 flex-1">
        {NAV_ITEMS.map((item) => (
          <SidebarItem key={item.href} {...item} collapsed={collapsed} />
        ))}
      </nav>
    </aside>
  );
}
