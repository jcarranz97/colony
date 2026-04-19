import { deleteAuthCookie } from "@/actions/auth.action";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export type ApiResponse<T> =
  | { success: true; data: T }
  | { success: false; error: { code: string; message: string } };

type ApiClientOptions = {
  token: string;
  method?: string;
  body?: string;
};

export async function apiClient<T>(
  path: string,
  { token, method = "GET", body }: ApiClientOptions,
): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
  };
  if (body) headers["Content-Type"] = "application/json";

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { method, headers, body });
  } catch {
    return {
      success: false,
      error: { code: "NETWORK_ERROR", message: "Network error" },
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

  if (response.status === 204 || method === "DELETE") {
    return { success: true, data: undefined as T };
  }

  try {
    const data: any = await response.json();
    if (!response.ok) {
      return {
        success: false,
        error: {
          code: "API_ERROR",
          message: data?.detail || data?.error?.message || "Request failed",
        },
      };
    }
    return { success: true, data: data as T };
  } catch {
    return {
      success: false,
      error: { code: "API_ERROR", message: response.statusText },
    };
  }
}

export async function loginUser(
  email: string,
  password: string,
): Promise<ApiResponse<any>> {
  const payload = new URLSearchParams();
  payload.append("username", email);
  payload.append("password", password);

  let response: Response;
  try {
    response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: payload,
    });
  } catch {
    return {
      success: false,
      error: { code: "NETWORK_ERROR", message: "Network error" },
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

  try {
    const data: any = await response.json();
    if (!response.ok) {
      return {
        success: false,
        error: { code: "API_ERROR", message: data?.detail || "Login failed" },
      };
    }
    return { success: true, data };
  } catch {
    return {
      success: false,
      error: { code: "API_ERROR", message: response.statusText },
    };
  }
}
