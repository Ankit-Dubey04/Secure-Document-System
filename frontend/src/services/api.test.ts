import { afterEach, describe, expect, it, vi } from "vitest";

import { api, downloadDocument, getTokens, setTokens } from "./api";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

describe("API client", () => {
  afterEach(() => { setTokens(null); vi.unstubAllGlobals(); });

  it("keeps tokens in session storage only", () => {
    setTokens({ access: "access", refresh: "refresh" });
    expect(getTokens()).toEqual({ access: "access", refresh: "refresh" });
    expect(localStorage.getItem("sentinel-vault.tokens")).toBeNull();
  });

  it("refreshes once after an expired access token then retries", async () => {
    setTokens({ access: "old", refresh: "refresh" });
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ detail: "Token is invalid" }, 401))
      .mockResolvedValueOnce(json({ access: "new", refresh: "rotated" }))
      .mockResolvedValueOnce(json({ id: 1, name: "Ada" }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(api<{ id: number }>("/auth/me/")).resolves.toEqual({ id: 1, name: "Ada" });
    expect(getTokens()).toEqual({ access: "new", refresh: "rotated" });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("clears the session when refresh fails", async () => {
    setTokens({ access: "old", refresh: "expired" });
    const expired = vi.fn();
    window.addEventListener("sentinel-vault:auth-expired", expired);
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(json({ detail: "Token invalid" }, 401))
      .mockResolvedValueOnce(json({ detail: "Token expired" }, 401)));
    await expect(api("/documents/")).rejects.toMatchObject({ status: 401 });
    expect(getTokens()).toBeNull();
    expect(expired).toHaveBeenCalledOnce();
    window.removeEventListener("sentinel-vault:auth-expired", expired);
  });

  it("sends real document uploads as multipart without overriding the boundary", async () => {
    setTokens({ access: "access", refresh: "refresh" });
    const fetchMock = vi.fn().mockResolvedValueOnce(json({ id: "document-id" }, 201));
    vi.stubGlobal("fetch", fetchMock);
    const form = new FormData(); form.append("title", "Evidence"); form.append("file", new File(["content"], "evidence.pdf", { type: "application/pdf" }));
    await api("/documents/", { method: "POST", body: form });
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.body).toBe(form);
    expect(new Headers(init.headers).has("Content-Type")).toBe(false);
  });

  it("surfaces a secure-download backend failure without creating a file", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(json({ detail: "Document cannot be retrieved securely." }, 422)));
    await expect(downloadDocument("document-id", "evidence.pdf")).rejects.toMatchObject({ status: 422, message: "Document cannot be retrieved securely." });
  });
});
