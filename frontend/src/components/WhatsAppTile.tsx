"use client";

import Link from "next/link";
import { useWaState } from "@/hooks/useWaState";

const LABELS: Record<string, string> = {
  disconnected: "Not connected",
  pairing: "Pairing...",
  ready: "Connected",
  error: "Error",
};

export default function WhatsAppTile() {
  const { waState, isLoading } = useWaState();
  const phase = waState?.state ?? "disconnected";
  const label = isLoading && !waState ? "..." : LABELS[phase] ?? phase;

  return (
    <Link
      href="/connect"
      className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-4 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition block"
    >
      <div className="text-xs uppercase tracking-wide text-zinc-500">
        WhatsApp
      </div>
      <div className="mt-1 text-lg font-medium">{label}</div>
    </Link>
  );
}
