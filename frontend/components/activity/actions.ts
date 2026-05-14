import { getAuthToken } from "@/actions/auth.action";
import type {
  ActivityEntry,
  ApiResponse,
  Comment,
  CreateCommentRequest,
  EntityType,
  UpdateCommentRequest,
} from "@/helpers/types";
import { fetchActivity, type ActivityQuery } from "@/lib/activity.api";
import {
  createComment,
  deleteComment,
  fetchComments,
  type CommentQuery,
  updateComment,
} from "@/lib/comments.api";

async function token() {
  return (await getAuthToken()) ?? "";
}

export const listActivityForEntity = async (
  entityType: EntityType,
  entityId: string,
  limit = 50,
): Promise<ApiResponse<ActivityEntry[]>> =>
  fetchActivity({ entityType, entityId, limit }, await token());

export const listActivityForCycle = async (
  cycleId: string,
  limit = 50,
): Promise<ApiResponse<ActivityEntry[]>> =>
  fetchActivity({ cycleId, limit }, await token());

export const listComments = async (
  query: CommentQuery,
): Promise<ApiResponse<Comment[]>> => fetchComments(query, await token());

export const addComment = async (
  payload: CreateCommentRequest,
): Promise<ApiResponse<Comment>> => createComment(payload, await token());

export const editComment = async (
  id: string,
  payload: UpdateCommentRequest,
): Promise<ApiResponse<Comment>> => updateComment(id, payload, await token());

export const removeComment = async (id: string): Promise<ApiResponse<void>> =>
  deleteComment(id, await token());
