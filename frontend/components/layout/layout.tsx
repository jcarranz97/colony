"use client";
import { usePathname, useRouter } from "next/navigation";
import { deleteAuthCookie } from "@/actions/auth.action";

const NAV_ITEMS = [
  { href: "/cycles", label: "Cycles", icon: "📅" },
  { href: "/payment-methods", label: "Payments", icon: "💳" },
  { href: "/expense-templates", label: "Templates", icon: "📋" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

const RING_COUNT = 16;

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = async () => {
    await deleteAuthCookie();
    router.push("/login");
  };

  return (
    <div className="nb-shell">
      {/* Cover bar */}
      <div className="nb-cover">
        <span className="nb-logo">Colony</span>
        <span className="nb-subtitle">household budget tracker</span>
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
          {NAV_ITEMS.map((item) => {
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
