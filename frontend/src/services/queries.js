import { api } from "./api.js";

export const queryKeys = {
  tree: ["pages", "tree"],
  page: (path) => ["pages", "by-path", path],
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
