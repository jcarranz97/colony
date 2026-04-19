"use client";
import { useTheme } from "next-themes";
import { Button } from "@heroui/react";
import { MdMenu, MdLightMode, MdDarkMode } from "react-icons/md";
import { useSidebar } from "@/components/layout/layout-context";
import { UserDropdown } from "./user-dropdown";

export function Navbar() {
  const { collapsed, setCollapsed } = useSidebar();
  const { theme, setTheme } = useTheme();

  return (
    <header className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex-shrink-0">
      <Button
        isIconOnly
        variant="ghost"
        size="sm"
        onPress={() => setCollapsed(!collapsed)}
        aria-label="Toggle sidebar"
      >
        <MdMenu className="text-xl" />
      </Button>

      <div className="flex items-center gap-2">
        <Button
          isIconOnly
          variant="ghost"
          size="sm"
          onPress={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Toggle theme"
        >
          {theme === "dark" ? (
            <MdLightMode className="text-xl" />
          ) : (
            <MdDarkMode className="text-xl" />
          )}
        </Button>
        <UserDropdown />
      </div>
    </header>
  );
}
