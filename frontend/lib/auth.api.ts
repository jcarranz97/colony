import { apiClient, loginUser, type ApiResponse } from "./api-client";
import type {
  UserResponse,
  AdminCreateUserRequest,
  AdminUpdateUserRequest,
} from "@/helpers/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function loginWithForm(username: string, password: string) {
  return loginUser(username, password);
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

export async function getCurrentUser(
  token: string,
): Promise<ApiResponse<UserResponse>> {
  return apiClient<UserResponse>("/auth/me", { token });
}

export async function listUsers(
  token: string,
): Promise<ApiResponse<UserResponse[]>> {
  return apiClient<UserResponse[]>("/auth/users", { token });
}

export async function createUser(
  token: string,
  data: AdminCreateUserRequest,
): Promise<ApiResponse<UserResponse>> {
  return apiClient<UserResponse>("/auth/register", {
    token,
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateUser(
  token: string,
  userId: string,
  data: AdminUpdateUserRequest,
): Promise<ApiResponse<UserResponse>> {
  return apiClient<UserResponse>(`/auth/users/${userId}`, {
    token,
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deactivateUser(
  token: string,
  userId: string,
): Promise<ApiResponse<void>> {
  return apiClient<void>(`/auth/users/${userId}`, {
    token,
    method: "DELETE",
  });
}

export async function reactivateUser(
  token: string,
  userId: string,
): Promise<ApiResponse<UserResponse>> {
  return apiClient<UserResponse>(`/auth/users/${userId}`, {
    token,
    method: "PUT",
    body: JSON.stringify({ active: true }),
  });
}
