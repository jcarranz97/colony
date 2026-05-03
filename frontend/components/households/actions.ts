import { getAuthToken } from "@/actions/auth.action";
import {
  listHouseholds,
  createHousehold,
  updateHousehold,
  deleteHousehold,
  getHouseholdMembers,
  addHouseholdMember,
  removeHouseholdMember,
  getMyHouseholds,
  setActiveHousehold,
} from "@/lib/households.api";
import type {
  CreateHouseholdRequest,
  UpdateHouseholdRequest,
  AddMemberRequest,
} from "@/helpers/types";

async function token() {
  return (await getAuthToken()) ?? "";
}

export const listHouseholdsAction = async () => listHouseholds(await token());

export const createHouseholdAction = async (payload: CreateHouseholdRequest) =>
  createHousehold(payload, await token());

export const updateHouseholdAction = async (
  id: string,
  payload: UpdateHouseholdRequest,
) => updateHousehold(id, payload, await token());

export const deleteHouseholdAction = async (id: string) =>
  deleteHousehold(id, await token());

export const getHouseholdMembersAction = async (id: string) =>
  getHouseholdMembers(id, await token());

export const addHouseholdMemberAction = async (
  householdId: string,
  payload: AddMemberRequest,
) => addHouseholdMember(householdId, payload, await token());

export const removeHouseholdMemberAction = async (
  householdId: string,
  userId: string,
) => removeHouseholdMember(householdId, userId, await token());

export const getMyHouseholdsAction = async () => getMyHouseholds(await token());

export const setActiveHouseholdAction = async (householdId: string) =>
  setActiveHousehold(householdId, await token());
