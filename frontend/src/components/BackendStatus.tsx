"use client";

import { useHealth } from "@/hooks/useHealth";

export default function BackendStatus() {
  const { health, isLoading, isError } = useHealth();

  let label: string;
  let tone: string;
  if (isLoading && !health) {
    label = "checking...";
    tone =
      "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";
  } else if (isError || !health?.ok) {
    label = "down";
    tone =
      "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300";
  } else {
    label = `ok v${health.version}`;
    tone =
      "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300";
  }

  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${tone}`}
    >
      Backend: {label}
    </span>
  );
}
