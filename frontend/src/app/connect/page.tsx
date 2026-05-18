"use client";

import { useEffect, useState } from "react";
import { useWaState } from "@/hooks/useWaState";

export default function ConnectPage() {
  const { waState, isLoading, connect, disconnect } = useWaState();
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!waState) return;
    if (waState.state === "disconnected" && !busy) {
      setBusy(true);
      connect()
        .catch(() => {
          // swallow; the state machine will surface last_error
        })
        .finally(() => setBusy(false));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [waState?.state]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Connect WhatsApp</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">
          Pair this app with WhatsApp on your phone. Single-user, single-device.
        </p>
      </header>

      {isLoading && !waState ? (
        <PanelMuted>Checking backend...</PanelMuted>
      ) : null}

      {waState?.state === "disconnected" && !busy ? (
        <PanelMuted>
          <div className="flex items-center justify-between gap-3">
            <span>Not connected yet.</span>
            <button
              type="button"
              onClick={() => connect()}
              className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
            >
              Start pairing
            </button>
          </div>
        </PanelMuted>
      ) : null}

      {waState?.state === "pairing" ? (
        <PairingPanel qrDataUrl={waState.qr_data_url} />
      ) : null}

      {waState?.state === "ready" ? (
        <ReadyPanel
          ownerPhone={waState.owner_phone}
          onDisconnect={() => disconnect()}
        />
      ) : null}

      {waState?.state === "error" ? (
        <ErrorPanel
          message={waState.last_error}
          onRetry={() => connect()}
        />
      ) : null}
    </div>
  );
}

function PanelMuted({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6 text-sm text-zinc-700 dark:text-zinc-300">
      {children}
    </div>
  );
}

function PairingPanel({ qrDataUrl }: { qrDataUrl: string | null }) {
  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
      <h2 className="text-base font-semibold">Scan the QR with WhatsApp</h2>
      <ol className="mt-2 text-sm text-zinc-600 dark:text-zinc-400 list-decimal pl-5 space-y-1">
        <li>Open WhatsApp on your phone.</li>
        <li>Tap Settings then Linked devices.</li>
        <li>Tap Link a device and scan this code.</li>
      </ol>
      <div className="mt-4 flex justify-center">
        {qrDataUrl ? (
          <img
            src={qrDataUrl}
            alt="WhatsApp pairing QR"
            className="h-72 w-72 rounded-md border border-zinc-200 dark:border-zinc-800 bg-white p-2"
          />
        ) : (
          <div className="h-72 w-72 rounded-md border border-dashed border-zinc-300 dark:border-zinc-700 flex items-center justify-center text-sm text-zinc-500">
            Waiting for QR...
          </div>
        )}
      </div>
      <p className="mt-3 text-xs text-zinc-500 text-center">
        WhatsApp rotates this code every 30 seconds. The page updates automatically.
      </p>
    </div>
  );
}

function ReadyPanel({
  ownerPhone,
  onDisconnect,
}: {
  ownerPhone: string | null;
  onDisconnect: () => void;
}) {
  return (
    <div className="rounded-lg border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950 p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-emerald-900 dark:text-emerald-200">
            WhatsApp connected
          </h2>
          <p className="mt-1 text-sm text-emerald-800 dark:text-emerald-300">
            Linked as {ownerPhone ?? "this device"}.
          </p>
        </div>
        <button
          type="button"
          onClick={onDisconnect}
          className="rounded-md border border-emerald-300 dark:border-emerald-800 bg-white dark:bg-zinc-900 px-3 py-1.5 text-sm font-medium text-emerald-700 dark:text-emerald-300 hover:bg-emerald-50 dark:hover:bg-zinc-800"
        >
          Disconnect
        </button>
      </div>
    </div>
  );
}

function ErrorPanel({
  message,
  onRetry,
}: {
  message: string | null;
  onRetry: () => void;
}) {
  return (
    <div className="rounded-lg border border-rose-200 dark:border-rose-900 bg-rose-50 dark:bg-rose-950 p-6">
      <h2 className="text-base font-semibold text-rose-900 dark:text-rose-200">
        Pairing failed
      </h2>
      <p className="mt-1 text-sm text-rose-800 dark:text-rose-300 break-all">
        {message ?? "Unknown error."}
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-3 rounded-md bg-rose-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-rose-700"
      >
        Retry
      </button>
    </div>
  );
}
