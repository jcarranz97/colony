import { getAuthToken } from "@/actions/auth.action";
import {
  fetchApiTokens,
  createApiToken,
  revokeApiToken,
} from "@/lib/api-tokens.api";
import type { CreateApiTokenRequest } from "@/helpers/types";

async function token() {
  return (await getAuthToken()) ?? "";
}

export const getApiTokens = async () => fetchApiTokens(await token());

export const addApiToken = async (payload: CreateApiTokenRequest) =>
  createApiToken(payload, await token());

export const removeApiToken = async (id: string) =>
  revokeApiToken(id, await token());
