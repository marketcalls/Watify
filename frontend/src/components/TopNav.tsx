"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import ThemeToggle from "@/components/ThemeToggle";
import { useAuth } from "@/hooks/useAuth";
import { useHealth } from "@/hooks/useHealth";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/connect", label: "Connect" },
  { href: "/groups", label: "Groups" },
  { href: "/send", label: "Send" },
  { href: "/history", label: "History" },
];

export default function TopNav() {
  const { user, isLoading, logout } = useAuth();
  const { health } = useHealth();
  // TKT-0046: hide Get started once the single admin is registered.
  const registered = health?.registered === true;
  const router = useRouter();
  const [signingOut, setSigningOut] = useState(false);

  async function onLogout() {
    setSigningOut(true);
    try {
      await logout();
      router.push("/");
    } finally {
      setSigningOut(false);
    }
  }

  return (
    <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/80 backdrop-blur">
      <nav
        aria-label="Main navigation"
        className="mx-auto max-w-6xl flex items-center gap-1 px-4 h-14"
      >
        <Link
          href={user ? "/dashboard" : "/"}
          className="text-base font-semibold tracking-tight mr-4"
        >
          Watify
        </Link>

        {isLoading ? (
          // Loading: brand only, no links. Avoids flash-of-wrong-state
          // on first paint while SWR resolves /api/auth/me.
          <span aria-hidden className="flex-1" />
        ) : user ? (
          <>
            <ul className="flex items-center gap-1 text-sm">
              {links.map((l) => (
                <li key={l.href}>
                  <Link
                    href={l.href}
                    className="px-3 py-1.5 rounded-md text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-900 transition"
                  >
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
            <div className="ml-auto flex items-center gap-3 text-sm">
              <ThemeToggle />
              <Link
                href="/profile"
                className="text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 underline-offset-4 hover:underline"
                title="Profile settings"
              >
                {user.username}
              </Link>
              <button
                type="button"
                onClick={onLogout}
                disabled={signingOut}
                className="px-3 py-1.5 rounded-md text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-900 transition disabled:opacity-50"
              >
                {signingOut ? "Signing out..." : "Logout"}
              </button>
            </div>
          </>
        ) : (
          <div className="ml-auto flex items-center gap-2 text-sm">
            <ThemeToggle />
            <Link
              href="/login"
              className="px-3 py-1.5 rounded-md text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-900 transition"
            >
              Sign in
            </Link>
            {!registered ? (
              <Link
                href="/register"
                className="rounded bg-zinc-900 dark:bg-zinc-100 text-zinc-50 dark:text-zinc-900 px-3 py-1.5 text-sm font-medium"
              >
                Get started
              </Link>
            ) : null}
          </div>
        )}
      </nav>
    </header>
  );
}
