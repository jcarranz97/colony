"use client";
import type { ApiResponse } from "@/helpers/types";
import { deleteAuthCookie } from "@/actions/auth.action";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function getTokenFromCookie(): string | undefined {
  if (typeof document === "undefined") return undefined;
  const match = document.cookie.match(/(?:^|;\s*)colony-token=([^;]*)/);
  return match ? match[1] : undefined;
}

export async function apiClient<T>(
  path: string,
  options: RequestInit & { token?: string } = {},
): Promise<ApiResponse<T>> {
  const { token: explicitToken, ...fetchOptions } = options;
  const token = explicitToken ?? getTokenFromCookie();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...fetchOptions, headers });
  } catch {
    return {
      success: false,
      error: {
        code: "NETWORK_ERROR",
        message: "Network error — check your connection",
      },
    };
  }

  if (response.status === 401) {
    await deleteAuthCookie();
    if (typeof window !== "undefined") window.location.href = "/login";
    return {
      success: false,
      error: { code: "UNAUTHORIZED", message: "Session expired" },
    };
  }

  if (!response.ok) {
    try {
      const body = await response.json();
      const err = body?.error ?? {};
      return {
        success: false,
        error: {
          code: err.code ?? "API_ERROR",
          message: err.message ?? "An error occurred",
        },
      };
    } catch {
      return {
        success: false,
        error: { code: "API_ERROR", message: response.statusText },
      };
    }
  }

  if (response.status === 204) return { success: true, data: undefined as T };

  const data: T = await response.json();
  return { success: true, data };
}
