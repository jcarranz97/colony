"use server";
import { getAuthToken } from "@/actions/auth.action";
import {
  listUsers,
  createUser,
  updateUser,
  deactivateUser,
  reactivateUser,
} from "@/lib/auth.api";
import type {
  AdminCreateUserRequest,
  AdminUpdateUserRequest,
} from "@/helpers/types";

export async function getUsersAction() {
  const token = await getAuthToken();
  if (!token)
    return {
      success: false as const,
      error: { code: "UNAUTHORIZED", message: "Not authenticated" },
    };
  return listUsers(token);
}

export async function createUserAction(data: AdminCreateUserRequest) {
  const token = await getAuthToken();
  if (!token)
    return {
      success: false as const,
      error: { code: "UNAUTHORIZED", message: "Not authenticated" },
    };
  return createUser(token, data);
}

export async function updateUserAction(
  userId: string,
  data: AdminUpdateUserRequest,
) {
  const token = await getAuthToken();
  if (!token)
    return {
      success: false as const,
      error: { code: "UNAUTHORIZED", message: "Not authenticated" },
    };
  return updateUser(token, userId, data);
}

export async function deactivateUserAction(userId: string) {
  const token = await getAuthToken();
  if (!token)
    return {
      success: false as const,
      error: { code: "UNAUTHORIZED", message: "Not authenticated" },
    };
  return deactivateUser(token, userId);
}

export async function reactivateUserAction(userId: string) {
  const token = await getAuthToken();
  if (!token)
    return {
      success: false as const,
      error: { code: "UNAUTHORIZED", message: "Not authenticated" },
    };
  return reactivateUser(token, userId);
}
