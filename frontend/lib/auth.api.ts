// Authentication API wrappers
import { apiClient } from "./api-client";

export async function loginWithForm(formData: any) {
  // Assuming 'apiClient' handles the full request cycle (credentials validation, token retrieval)
  return apiClient("/auth/login", formData);
}

export async function register(formData: any) {
  // Assuming a specific endpoint for registration exists
  return apiClient("/auth/register", formData);
}
