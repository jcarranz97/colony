"use client";
import { useRouter } from "next/navigation";
import { Avatar, Button, Popover, Menu } from "@heroui/react";
import { deleteAuthCookie } from "@/actions/auth.action";

export function UserDropdown() {
  const router = useRouter();

  const handleLogout = async () => {
    await deleteAuthCookie();
    router.push("/login");
  };

  return (
    <Popover>
      <Popover.Trigger>
        <Avatar className="cursor-pointer size-8">
          <Avatar.Fallback>U</Avatar.Fallback>
        </Avatar>
      </Popover.Trigger>
      <Popover.Content>
        <Popover.Dialog>
          <Menu
            onAction={(key) => {
              if (key === "settings") router.push("/settings");
              if (key === "logout") handleLogout();
            }}
          >
            <Menu.Item id="settings">Settings</Menu.Item>
            <Menu.Item id="logout">Sign Out</Menu.Item>
          </Menu>
        </Popover.Dialog>
      </Popover.Content>
    </Popover>
  );
}
