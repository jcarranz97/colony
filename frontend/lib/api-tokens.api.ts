import { apiClient } from "./api-client";
import type {
  ApiToken,
  ApiTokenWithSecret,
  CreateApiTokenRequest,
} from "@/helpers/types";

export const fetchApiTokens = (token: string) =>
  apiClient<ApiToken[]>("/api-tokens/", { token });

export const createApiToken = (payload: CreateApiTokenRequest, token: string) =>
  apiClient<ApiTokenWithSecret>("/api-tokens/", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });

export const revokeApiToken = (tokenId: string, token: string) =>
  apiClient<void>(`/api-tokens/${tokenId}`, {
    method: "DELETE",
    token,
  });
