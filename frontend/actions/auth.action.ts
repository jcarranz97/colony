"use server";
import { cookies } from "next/headers";

export const createAuthCookie = async (token: string) => {
  (await cookies()).set("colony-token", token, {
    httpOnly: true,
    secure: process.env.COOKIE_SECURE === "true",
    sameSite: "lax",
    path: "/",
    maxAge: 30 * 60,
  });
};

export const deleteAuthCookie = async () => {
  (await cookies()).delete("colony-token");
};

export const getAuthToken = async (): Promise<string | undefined> => {
  return (await cookies()).get("colony-token")?.value;
};
