import { loginUser, type ApiResponse } from "./api-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function loginWithForm(email: string, password: string) {
  return loginUser(email, password);
}

export async function register(formData: any): Promise<ApiResponse<any>> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    });
  } catch {
    return {
      success: false,
      error: { code: "NETWORK_ERROR", message: "Network error" },
    };
  }

  try {
    const data: any = await response.json();
    if (!response.ok) {
      return {
        success: false,
        error: {
          code: "API_ERROR",
          message: data?.detail || "Registration failed",
        },
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
