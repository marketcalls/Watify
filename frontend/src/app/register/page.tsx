"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { mutate } from "swr";
import { ApiError, auth } from "@/lib/api";

type ErrorState =
  | null
  | { kind: "closed" }
  | { kind: "not_configured" }
  | { kind: "validation"; message: string }
  | { kind: "generic"; message: string };

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
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
    if (password !== confirm) {
      setErr({ kind: "validation", message: "Passwords do not match." });
      return;
    }
    setSubmitting(true);
    try {
      await auth.register(u, password);
      // TKT-0045: invalidate /api/auth/me cache before navigating so
      // RequireAuth on /dashboard sees the fresh user immediately.
      await mutate("/api/auth/me");
      router.push("/dashboard");
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.status === 409) setErr({ kind: "closed" });
        else if (e.status === 503) setErr({ kind: "not_configured" });
        else if (e.status === 422) setErr({ kind: "validation", message: "The backend rejected the form. Check username and password." });
        else setErr({ kind: "generic", message: `HTTP ${e.status}` });
      } else {
        setErr({ kind: "generic", message: e instanceof Error ? e.message : "network error" });
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (err && err.kind === "closed") {
    return (
      <div className="mx-auto w-full max-w-sm">
        <h1 className="text-2xl font-semibold mb-1">App already registered</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-6">
          Watify is single-user. The admin account has already been created on this install. Sign in instead.
        </p>
        <Link
          href="/login"
          className="inline-block rounded bg-zinc-900 dark:bg-zinc-100 text-zinc-50 dark:text-zinc-900 px-4 py-2 text-sm font-medium"
        >
          Go to sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-sm">
      <h1 className="text-2xl font-semibold mb-1">Create the admin account</h1>
      <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-6">
        Watify is single-user; only one account can be registered. Pick a strong password -- you will not be able to reset it from this UI.
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
            autoComplete="new-password"
            required
            minLength={12}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 text-sm"
          />
          <p className="mt-1 text-xs text-zinc-500">At least 12 characters.</p>
        </div>
        <div>
          <label htmlFor="confirm" className="block text-sm font-medium mb-1">
            Confirm password
          </label>
          <input
            id="confirm"
            name="confirm"
            type="password"
            autoComplete="new-password"
            required
            minLength={12}
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 text-sm"
          />
        </div>

        {err && <ErrorPanel state={err} />}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded bg-zinc-900 dark:bg-zinc-100 text-zinc-50 dark:text-zinc-900 px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {submitting ? "Creating account..." : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-sm text-zinc-600 dark:text-zinc-400">
        Already registered?{" "}
        <Link href="/login" className="underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}

function ErrorPanel({ state }: { state: Exclude<NonNullable<ErrorState>, { kind: "closed" }> }) {
  let body: string;
  switch (state.kind) {
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
