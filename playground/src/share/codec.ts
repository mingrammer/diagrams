import { deflate, inflate } from "pako";

const PREFIX = "#code=";

export function encodeShare(code: string): string {
  const compressed = deflate(new TextEncoder().encode(code), { level: 9 });
  let binary = "";
  for (const byte of compressed) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function decodeShare(fragment: string): string | null {
  let value = fragment.startsWith(PREFIX) ? fragment.slice(PREFIX.length) : fragment;
  value = value.replace(/^#/, "");
  if (!value) return null;
  try {
    const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
    // encodeShare strips base64 padding; atob() requires it in some engines,
    // so restore it to a multiple of 4 before decoding.
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    const binary = atob(padded);
    const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
    return new TextDecoder().decode(inflate(bytes));
  } catch {
    return null;
  }
}
