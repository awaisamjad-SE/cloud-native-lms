import { getApiBase } from "./api";

export function resolveMediaUrl(value?: string | null): string {
  if (!value) return "";
  const cleanValue = value.trim();
  if (!cleanValue) return "";
  if (/^(https?:|data:|blob:)/i.test(cleanValue)) return cleanValue;
  if (cleanValue.startsWith("//")) return `https:${cleanValue}`;

  try {
    return `${new URL(getApiBase()).origin}/${cleanValue.replace(/^\/+/, "")}`;
  } catch {
    return `/${cleanValue.replace(/^\/+/, "")}`;
  }
}