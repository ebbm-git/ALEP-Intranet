import { api } from "./api.js";

export const queryKeys = {
  tree: ["pages", "tree"],
  page: (path) => ["pages", "by-path", path],
  versions: (blockId) => ["content-blocks", blockId, "versions"],
};

export const fetchTree = async () => {
  const { data } = await api.get("/pages/tree");
  return data;
};

export const fetchPageByPath = async (path) => {
  const { data } = await api.get(`/pages/by-path/${path}`);
  return data;
};

export const updateBlock = async ({ id, body }) => {
  const { data } = await api.patch(`/content-blocks/${id}`, { body });
  return data;
};

export const insertBlock = async ({ anchorId, where, body = "" }) => {
  const { data } = await api.post(`/content-blocks/${anchorId}/insert-${where}`, { body });
  return data;
};

export const deleteBlock = async (id) => {
  await api.delete(`/content-blocks/${id}`);
};

export const appendBlock = async ({ pageId, body = "" }) => {
  const { data } = await api.post(`/content-blocks`, {
    page_id: pageId,
    body,
    block_type: "markdown",
  });
  return data;
};

export const fetchVersions = async (blockId) => {
  const { data } = await api.get(`/content-blocks/${blockId}/versions`);
  return data;
};

export const restoreVersion = async ({ blockId, version }) => {
  const { data } = await api.post(`/content-blocks/${blockId}/restore/${version}`);
  return data;
};

// ---------- Admin ----------

export const adminQueryKeys = {
  users: ["admin", "users"],
  permissions: ["admin", "permissions"],
};

export const fetchAdminUsers = async () => {
  const { data } = await api.get("/admin/users");
  return data;
};

export const createUser = async ({ email, password, fullName, role }) => {
  const { data } = await api.post(`/admin/users`, {
    email,
    password,
    full_name: fullName || null,
    role,
  });
  return data;
};

export const updateUserRole = async ({ userId, role }) => {
  const { data } = await api.patch(`/admin/users/${userId}`, { role });
  return data;
};

export const deleteUser = async (userId) => {
  await api.delete(`/admin/users/${userId}`);
};

export const fetchPermissions = async () => {
  const { data } = await api.get("/admin/permissions");
  return data;
};

export const setPermissionCell = async ({ role, pageId, hasAccess }) => {
  const { data } = await api.post("/admin/permissions", {
    role,
    page_id: pageId,
    has_access: hasAccess,
  });
  return data;
};

export const bulkReplacePermissions = async (cells) => {
  const { data } = await api.put("/admin/permissions/bulk", cells);
  return data;
};
