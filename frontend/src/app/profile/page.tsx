"use client";

import { useState } from "react";
import { mutate } from "swr";
import RequireAuth from "@/components/RequireAuth";
import { toast } from "@/components/Toaster";
import { useAuth } from "@/hooks/useAuth";
import { ApiError, auth } from "@/lib/api";

export default function ProfilePage() {
  return (
    <RequireAuth>
      <ProfileInner />
    </RequireAuth>
  );
}

function ProfileInner() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Profile</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">
          Signed in as <span className="font-medium">{user?.username}</span>. Changes invalidate
          other sessions.
        </p>
      </header>

      <UsernameCard currentUsername={user?.username ?? ""} />
      <PasswordCard />
    </div>
  );
}

// ---- shared error mapping -------------------------------------------

type FormError =
  | { kind: "validation"; message: string }
  | { kind: "invalid_password" }
  | { kind: "username_taken" }
  | { kind: "no_changes" }
  | { kind: "rate_limited" }
  | { kind: "generic"; message: string };

function fromApiError(e: unknown): FormError {
  if (e instanceof ApiError) {
    if (e.status === 401) return { kind: "invalid_password" };
    if (e.status === 409) return { kind: "username_taken" };
    if (e.status === 422) return { kind: "no_changes" };
    if (e.status === 429) return { kind: "rate_limited" };
    return { kind: "generic", message: `HTTP ${e.status}` };
  }
  return { kind: "generic", message: e instanceof Error ? e.message : "network error" };
}

function errorText(err: FormError): string {
  switch (err.kind) {
    case "validation":
      return err.message;
    case "invalid_password":
      return "Current password is wrong.";
    case "username_taken":
      return "That username is already in use.";
    case "no_changes":
      return "Nothing to update -- the value matches the current one.";
    case "rate_limited":
      return "Too many attempts. Wait a minute and try again.";
    case "generic":
      return err.message;
  }
}

function ErrorPanel({ err }: { err: FormError }) {
  return (
    <div
      role="alert"
      className="rounded border border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950 text-red-800 dark:text-red-200 px-3 py-2 text-sm"
    >
      {errorText(err)}
    </div>
  );
}

// ---- username card --------------------------------------------------

function UsernameCard({ currentUsername }: { currentUsername: string }) {
  const [newUsername, setNewUsername] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<FormError | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    const u = newUsername.trim();
    if (u.length === 0) {
      setErr({ kind: "validation", message: "New username is required." });
      return;
    }
    if (u === currentUsername) {
      setErr({ kind: "validation", message: "New username matches the current one." });
      return;
    }
    if (currentPassword.length === 0) {
      setErr({ kind: "validation", message: "Current password is required." });
      return;
    }
    setSubmitting(true);
    try {
      await auth.updateProfile({ current_password: currentPassword, new_username: u });
      await mutate("/api/auth/me");
      setNewUsername("");
      setCurrentPassword("");
      toast.success("Username updated.");
    } catch (e) {
      setErr(fromApiError(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
      <h2 className="text-base font-semibold">Change username</h2>
      <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
        Pick something memorable. You will use it on the next sign in.
      </p>

      <form onSubmit={onSubmit} className="mt-4 space-y-4 max-w-sm" noValidate>
        <div>
          <label htmlFor="username-current" className="block text-sm font-medium mb-1">
            Current username
          </label>
          <input
            id="username-current"
            type="text"
            value={currentUsername}
            disabled
            className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-zinc-800 text-zinc-500 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="username-new" className="block text-sm font-medium mb-1">
            New username
          </label>
          <input
            id="username-new"
            name="username"
            type="text"
            autoComplete="username"
            required
            value={newUsername}
            onChange={(e) => setNewUsername(e.target.value)}
            className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="username-current-pw" className="block text-sm font-medium mb-1">
            Current password
          </label>
          <input
            id="username-current-pw"
            name="current-password-username"
            type="password"
            autoComplete="current-password"
            required
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 text-sm"
          />
        </div>

        {err && <ErrorPanel err={err} />}

        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-zinc-900 dark:bg-zinc-100 text-zinc-50 dark:text-zinc-900 px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {submitting ? "Saving..." : "Save username"}
        </button>
      </form>
    </section>
  );
}

// ---- password card --------------------------------------------------

function PasswordCard() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<FormError | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    if (newPassword.length < 12) {
      setErr({ kind: "validation", message: "New password must be at least 12 characters." });
      return;
    }
    if (newPassword !== confirm) {
      setErr({ kind: "validation", message: "Passwords do not match." });
      return;
    }
    if (currentPassword.length === 0) {
      setErr({ kind: "validation", message: "Current password is required." });
      return;
    }
    if (currentPassword === newPassword) {
      setErr({ kind: "validation", message: "New password matches the current one." });
      return;
    }
    setSubmitting(true);
    try {
      await auth.updateProfile({
        current_password: currentPassword,
        new_password: newPassword,
      });
      await mutate("/api/auth/me");
      setCurrentPassword("");
      setNewPassword("");
      setConfirm("");
      toast.success("Password updated.");
    } catch (e) {
      setErr(fromApiError(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
      <h2 className="text-base font-semibold">Change password</h2>
      <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
        At least 12 characters. There is no recovery -- pick something you can remember.
      </p>

      <form onSubmit={onSubmit} className="mt-4 space-y-4 max-w-sm" noValidate>
        <div>
          <label htmlFor="pw-current" className="block text-sm font-medium mb-1">
            Current password
          </label>
          <input
            id="pw-current"
            name="current-password"
            type="password"
            autoComplete="current-password"
            required
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="pw-new" className="block text-sm font-medium mb-1">
            New password
          </label>
          <input
            id="pw-new"
            name="new-password"
            type="password"
            autoComplete="new-password"
            required
            minLength={12}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 text-sm"
          />
          <p className="mt-1 text-xs text-zinc-500">At least 12 characters.</p>
        </div>
        <div>
          <label htmlFor="pw-confirm" className="block text-sm font-medium mb-1">
            Confirm new password
          </label>
          <input
            id="pw-confirm"
            name="confirm-password"
            type="password"
            autoComplete="new-password"
            required
            minLength={12}
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className="w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 text-sm"
          />
        </div>

        {err && <ErrorPanel err={err} />}

        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-zinc-900 dark:bg-zinc-100 text-zinc-50 dark:text-zinc-900 px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {submitting ? "Saving..." : "Save password"}
        </button>
      </form>
    </section>
  );
}
