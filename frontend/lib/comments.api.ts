import type {
  Comment,
  CreateCommentRequest,
  EntityType,
  UpdateCommentRequest,
} from "@/helpers/types";

import { apiClient } from "./api-client";

export interface CommentQuery {
  entityType?: EntityType;
  entityId?: string;
  cycleId?: string;
  limit?: number;
  before?: string;
}

function buildQueryString(q: CommentQuery): string {
  const params = new URLSearchParams();
  if (q.entityType) params.set("entity_type", q.entityType);
  if (q.entityId) params.set("entity_id", q.entityId);
  if (q.cycleId) params.set("cycle_id", q.cycleId);
  if (q.limit !== undefined) params.set("limit", String(q.limit));
  if (q.before) params.set("before", q.before);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export const fetchComments = (q: CommentQuery, token: string) =>
  apiClient<Comment[]>(`/comments/${buildQueryString(q)}`, { token });

export const createComment = (payload: CreateCommentRequest, token: string) =>
  apiClient<Comment>("/comments/", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });

export const updateComment = (
  id: string,
  payload: UpdateCommentRequest,
  token: string,
) =>
  apiClient<Comment>(`/comments/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    token,
  });

export const deleteComment = (id: string, token: string) =>
  apiClient<void>(`/comments/${id}`, {
    method: "DELETE",
    token,
  });
