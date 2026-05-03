import { apiClient } from "./api-client";
import type {
  HouseholdResponse,
  HouseholdMemberResponse,
  CreateHouseholdRequest,
  UpdateHouseholdRequest,
  AddMemberRequest,
} from "@/helpers/types";

export const listHouseholds = (token: string) =>
  apiClient<HouseholdResponse[]>("/households/", { token });

export const createHousehold = (
  payload: CreateHouseholdRequest,
  token: string,
) =>
  apiClient<HouseholdResponse>("/households/", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });

export const getHousehold = (id: string, token: string) =>
  apiClient<HouseholdResponse>(`/households/${id}`, { token });

export const updateHousehold = (
  id: string,
  payload: UpdateHouseholdRequest,
  token: string,
) =>
  apiClient<HouseholdResponse>(`/households/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    token,
  });

export const deleteHousehold = (id: string, token: string) =>
  apiClient<void>(`/households/${id}`, { method: "DELETE", token });

export const getHouseholdMembers = (id: string, token: string) =>
  apiClient<HouseholdMemberResponse[]>(`/households/${id}/members`, { token });

export const addHouseholdMember = (
  id: string,
  payload: AddMemberRequest,
  token: string,
) =>
  apiClient<void>(`/households/${id}/members`, {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });

export const removeHouseholdMember = (
  householdId: string,
  userId: string,
  token: string,
) =>
  apiClient<void>(`/households/${householdId}/members/${userId}`, {
    method: "DELETE",
    token,
  });

export const getMyHouseholds = (token: string) =>
  apiClient<HouseholdResponse[]>("/households/me", { token });

export const setActiveHousehold = (householdId: string, token: string) =>
  apiClient<HouseholdResponse>("/households/me/active", {
    method: "PUT",
    body: JSON.stringify({ household_id: householdId }),
    token,
  });
