"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ApiError, auth } from "@/lib/api";

// TKT-0029: honor the `?next=` query param post-login, but only when
// it is a same-origin path. Anything else (absolute URLs, protocol-
// relative `//evil.com`, paths with `:` that browsers interpret as a
// scheme, or non-strings) falls back to the safe default.
function safeNextPath(raw: string | null): string {
  const fallback = "/dashboard";
  if (typeof raw !== "string") return fallback;
  if (!raw.startsWith("/")) return fallback;     // must be a path
  if (raw.startsWith("//")) return fallback;     // protocol-relative
  if (raw.includes(":")) return fallback;        // would-be scheme
  return raw;
}

type ErrorState =
  | null
  | { kind: "invalid" }
  | { kind: "locked"; retryAfter: number }
  | { kind: "not_configured" }
  | { kind: "validation"; message: string }
  | { kind: "generic"; message: string };

function parseRetryAfter(body: unknown): number {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail?: unknown }).detail;
    if (detail && typeof detail === "object" && "retry_after" in detail) {
      const v = (detail as { retry_after?: unknown }).retry_after;
      if (typeof v === "number" && Number.isFinite(v)) return Math.max(1, Math.ceil(v));
    }
  }
  return 60;
}

// TKT-0033: useSearchParams() must sit inside a Suspense boundary so
// Next.js 16's static prerender can opt the page into client-side
// rendering instead of failing the production build. Default export
// is the Suspense wrapper; the actual form lives in LoginForm below.
export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<ErrorState>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    const u = username.trim();
    if (u.length === 0) {
      setErr({ kind: "validation", message: "Username is required." });
      return;
    }
    if (password.length < 12) {
      setErr({ kind: "validation", message: "Password must be at least 12 characters." });
      return;
    }
    setSubmitting(true);
    try {
      await auth.login(u, password);
      router.push(safeNextPath(searchParams.get("next")));
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.status === 401) setErr({ kind: "invalid" });
        else if (e.status === 429) setErr({ kind: "locked", retryAfter: parseRetryAfter(e.body) });
        else if (e.status === 503) setErr({ kind: "not_configured" });
        else setErr({ kind: "generic", message: `HTTP ${e.status}` });
      } else {
        setErr({ kind: "generic", message: e instanceof Error ? e.message : "network error" });
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-sm">
      <h1 className="text-2xl font-semibold mb-1">Sign in</h1>
      <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-6">
        Watify is a single-user app. Enter your admin credentials.
      </p>

      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <div>
          <label htmlFor="username" className="block text-sm font-medium mb-1">
            Username
          </label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium mb-1">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            minLength={12}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 text-sm"
          />
          <p className="mt-1 text-xs text-zinc-500">At least 12 characters.</p>
        </div>

        {err && <ErrorPanel state={err} />}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded bg-zinc-900 dark:bg-zinc-100 text-zinc-50 dark:text-zinc-900 px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {submitting ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <p className="mt-6 text-sm text-zinc-600 dark:text-zinc-400">
        No account yet?{" "}
        <Link href="/register" className="underline">
          Create the admin account
        </Link>
      </p>
    </div>
  );
}

function ErrorPanel({ state }: { state: NonNullable<ErrorState> }) {
  let body: string;
  switch (state.kind) {
    case "invalid":
      body = "Invalid username or password.";
      break;
    case "locked":
      body = `Too many attempts, try again in ${state.retryAfter} seconds.`;
      break;
    case "not_configured":
      body = "Auth is not configured on the backend. Set WATIFY_APP_SECRET in backend/.env and restart.";
      break;
    case "validation":
    case "generic":
      body = state.message;
      break;
  }
  return (
    <div
      role="alert"
      className="rounded border border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950 text-red-800 dark:text-red-200 px-3 py-2 text-sm"
    >
      {body}
    </div>
  );
}
