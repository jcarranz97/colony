import type { ActivityEntry, EntityType } from "@/helpers/types";

import { apiClient } from "./api-client";

export interface ActivityQuery {
  entityType?: EntityType;
  entityId?: string;
  cycleId?: string;
  limit?: number;
  before?: string;
}

function buildQueryString(q: ActivityQuery): string {
  const params = new URLSearchParams();
  if (q.entityType) params.set("entity_type", q.entityType);
  if (q.entityId) params.set("entity_id", q.entityId);
  if (q.cycleId) params.set("cycle_id", q.cycleId);
  if (q.limit !== undefined) params.set("limit", String(q.limit));
  if (q.before) params.set("before", q.before);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export const fetchActivity = (q: ActivityQuery, token: string) =>
  apiClient<ActivityEntry[]>(`/activity/${buildQueryString(q)}`, { token });
