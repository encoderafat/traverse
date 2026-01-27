import { getAccessToken } from "./auth";

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = await getAccessToken();

  return fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: token ? `Bearer ${token}` : "",
      "Content-Type": "application/json",
    },
  });
}
