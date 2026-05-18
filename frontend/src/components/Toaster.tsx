"use client";

// TKT-0008: global toast queue.
// Module-level singleton store (no external deps). Subscribers
// re-render via useSyncExternalStore. The exported `toast` object
// can be called from anywhere (hooks, page components, error
// handlers). The mounted <Toaster /> component renders the stack.
//
// Inline error text remains the source of truth for accessibility
// and persistence; toasts are auxiliary.

import { useSyncExternalStore } from "react";

type ToastKind = "success" | "error";

type Toast = {
  id: number;
  kind: ToastKind;
  text: string;
  duration: number;
};

type Listener = () => void;

// TKT-0036: useSyncExternalStore expects getSnapshot/getServerSnapshot
// to return the SAME reference between calls when nothing has changed.
// Returning a fresh `[]` literal from getServerSnapshot would create a
// new identity on every render and tip React into the
// "result of getServerSnapshot should be cached" warning + a re-render
// loop. EMPTY is a single frozen reference reused on every server-pass
// call; the runtime store starts as the same empty array.
const EMPTY: Toast[] = Object.freeze([]) as unknown as Toast[];

let toasts: Toast[] = EMPTY;
let nextId = 1;
const listeners = new Set<Listener>();

function notify() {
  for (const l of listeners) l();
}

function add(kind: ToastKind, text: string, opts?: { duration?: number }): number {
  const duration = opts?.duration ?? 4000;
  const id = nextId++;
  toasts = [...toasts, { id, kind, text, duration }];
  notify();
  if (typeof window !== "undefined" && duration > 0) {
    window.setTimeout(() => dismiss(id), duration);
  }
  return id;
}

function dismiss(id: number) {
  const before = toasts.length;
  toasts = toasts.filter((t) => t.id !== id);
  if (toasts.length !== before) notify();
}

function subscribe(l: Listener): () => void {
  listeners.add(l);
  return () => {
    listeners.delete(l);
  };
}

function getSnapshot(): Toast[] {
  return toasts;
}

function getServerSnapshot(): Toast[] {
  return EMPTY;
}

export const toast = {
  success: (text: string, opts?: { duration?: number }) => add("success", text, opts),
  error: (text: string, opts?: { duration?: number }) => add("error", text, opts),
  dismiss,
};

export default function Toaster() {
  const items = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  if (items.length === 0) return null;

  return (
    <div
      aria-live="polite"
      aria-atomic="false"
      className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
    >
      {items.map((t) => (
        <div
          key={t.id}
          role={t.kind === "error" ? "alert" : "status"}
          className={
            "pointer-events-auto rounded border-l-4 bg-white dark:bg-zinc-900 shadow-md px-4 py-3 text-sm " +
            (t.kind === "error"
              ? "border-red-500 text-red-800 dark:text-red-200"
              : "border-emerald-500 text-emerald-800 dark:text-emerald-200")
          }
        >
          <button
            type="button"
            onClick={() => dismiss(t.id)}
            className="float-right ml-3 text-xs text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
            aria-label="Dismiss"
          >
            close
          </button>
          {t.text}
        </div>
      ))}
    </div>
  );
}
