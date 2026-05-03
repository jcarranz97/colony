"use client";
import { usePathname, useRouter } from "next/navigation";
import { deleteAuthCookie, getAuthToken } from "@/actions/auth.action";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { getCurrentUser } from "@/lib/auth.api";
import { getMyHouseholds } from "@/lib/households.api";
import type { UserResponse } from "@/helpers/types";

const BASE_NAV_ITEMS = [
  { href: "/cycles", label: "Cycles", icon: "📅" },
  { href: "/payment-methods", label: "Payment Methods", icon: "💳" },
  { href: "/recurrent-expenses", label: "Recurrent Expenses", icon: "📋" },
  { href: "/incomes", label: "Incomes", icon: "💰" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

const ADMIN_NAV_ITEMS = [
  { href: "/users", label: "Users", icon: "👥" },
  { href: "/households", label: "Households", icon: "🏠" },
];

const RING_COUNT = 16;

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserResponse | null>(null);
  const [activeHouseholdName, setActiveHouseholdName] = useState<string | null>(
    null,
  );

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const fetchUser = async () => {
      const token = await getAuthToken();
      if (!token) return;
      const result = await getCurrentUser(token);
      if (!result.success) return;
      setCurrentUser(result.data);
      const activeId = result.data.active_household_id;
      if (!activeId) return;
      const hhResult = await getMyHouseholds(token);
      if (hhResult.success) {
        const active = hhResult.data.find((h) => h.id === activeId);
        if (active) setActiveHouseholdName(active.name);
      }
    };
    fetchUser();
  }, []);

  const handleLogout = async () => {
    await deleteAuthCookie();
    router.push("/login");
  };

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  const navItems =
    currentUser?.role === "admin"
      ? [...BASE_NAV_ITEMS, ...ADMIN_NAV_ITEMS]
      : BASE_NAV_ITEMS;

  return (
    <div className="nb-shell">
      {/* Cover bar */}
      <div className="nb-cover">
        <span className="nb-logo">Colony</span>
        <span className="nb-subtitle">
          household budget tracker
          {activeHouseholdName && (
            <span
              style={{
                marginLeft: 10,
                paddingLeft: 10,
                borderLeft: "1px solid rgba(201,168,76,0.5)",
                color: "var(--cover-accent)",
                fontFamily: "var(--font-title)",
                fontWeight: 600,
                fontSize: "1.05em",
              }}
            >
              🏠 {activeHouseholdName}
            </span>
          )}
        </span>
        {mounted && (
          <button
            className="nb-theme-toggle"
            onClick={toggleTheme}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            {theme === "dark" ? "☀️" : "🌙"}
          </button>
        )}
        <button className="nb-signout" onClick={handleLogout}>
          Sign out
        </button>
      </div>

      {/* Body: spiral + nav + page */}
      <div className="nb-body">
        {/* Spiral binding */}
        <div className="nb-spiral">
          {Array.from({ length: RING_COUNT }).map((_, i) => (
            <div key={i} className="nb-ring" />
          ))}
        </div>

        {/* Navigation tabs */}
        <nav className="nb-nav">
          {navItems.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <button
                key={item.href}
                className={`nb-tab${isActive ? " nb-tab-active" : ""}`}
                onClick={() => router.push(item.href)}
              >
                <span>{item.icon}</span>
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Page content with ruled lines */}
        <div className="nb-page">
          <div className="nb-lines" />
          <div className="nb-margin" />
          <div className="nb-content">{children}</div>
        </div>
      </div>
    </div>
  );
}
