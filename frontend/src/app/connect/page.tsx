"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import PairCodePanel from "@/components/connect/PairCodePanel";
import RequireAuth from "@/components/RequireAuth";
import { toast } from "@/components/Toaster";
import { useWaState } from "@/hooks/useWaState";
import { ApiError, wa } from "@/lib/api";

const AUTO_FLAG = "watify.autopair.started";

export default function ConnectPage() {
  return (
    <RequireAuth>
      <ConnectInner />
    </RequireAuth>
  );
}

type Mode = "qr" | "code";

function ConnectInner() {
  const { waState, isLoading, connect, disconnect } = useWaState();
  const [busy, setBusy] = useState(false);
  const autoStarted = useRef(false);
  // TKT-0035: pair-code mode. Local-only state; refreshing the page
  // resets back to QR mode, which mirrors the legacy behavior.
  const [mode, setMode] = useState<Mode>("qr");
  const [phoneDraft, setPhoneDraft] = useState("");
  const [codeErr, setCodeErr] = useState<string | null>(null);

  // Auto-pair once per mount / per session. Three layers of guard so dev
  // hot-reloads do not stampede /api/wa/connect:
  //   1. useRef survives within a single mount.
  //   2. sessionStorage flag survives Fast Refresh remounts.
  //   3. We only auto-start when state is "disconnected" -- if the wars
  //      worker is already pairing or ready we never touch it.
  useEffect(() => {
    if (!waState) return;
    if (autoStarted.current) return;
    if (typeof window !== "undefined" && sessionStorage.getItem(AUTO_FLAG)) {
      autoStarted.current = true;
      return;
    }
    if (waState.state !== "disconnected") {
      // Already pairing/ready/error -- treat as if auto-pair fired.
      autoStarted.current = true;
      if (typeof window !== "undefined") {
        sessionStorage.setItem(AUTO_FLAG, "1");
      }
      return;
    }
    autoStarted.current = true;
    if (typeof window !== "undefined") {
      sessionStorage.setItem(AUTO_FLAG, "1");
    }
    setBusy(true);
    connect()
      .catch(() => {
        // swallow; the state machine will surface last_error
      })
      .finally(() => setBusy(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [waState?.state]);

  async function handleDisconnect() {
    // TKT-0050: keep AUTO_FLAG set so the disconnected->auto-pair
    // loop does not fire immediately after an explicit disconnect.
    // The operator can still re-pair manually via "Start pairing".
    autoStarted.current = true;
    if (typeof window !== "undefined") {
      sessionStorage.setItem(AUTO_FLAG, "1");
    }
    await disconnect();
  }

  async function handleManualConnect() {
    autoStarted.current = true;
    if (typeof window !== "undefined") {
      sessionStorage.setItem(AUTO_FLAG, "1");
    }
    await connect();
  }

  async function handlePairCodeConnect() {
    setCodeErr(null);
    const phone = phoneDraft.trim();
    if (!phone.startsWith("+") || phone.length < 8 || phone.length > 16) {
      setCodeErr("Phone must start with + and be 8-16 characters (E.164).");
      return;
    }
    autoStarted.current = true;
    if (typeof window !== "undefined") {
      sessionStorage.setItem(AUTO_FLAG, "1");
    }
    setBusy(true);
    try {
      await connect(phone);
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) {
        const detail =
          e.body && typeof e.body === "object" && "detail" in e.body
            ? String((e.body as { detail?: unknown }).detail ?? "invalid phone")
            : "invalid phone";
        setCodeErr(detail);
        toast.error(detail);
      } else {
        const msg = e instanceof Error ? e.message : "network error";
        setCodeErr(msg);
        toast.error(msg);
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleModeChange(next: Mode) {
    if (next === mode) return;
    setMode(next);
    setCodeErr(null);
    // If currently pairing, flipping modes means we need to reset the
    // wars worker so it asks for the right callback again. The /connect
    // POST without a body resumes the QR path; the user explicitly
    // clicks "Get pair code" for the code path.
    if (next === "qr" && waState?.state === "pairing") {
      setBusy(true);
      try {
        await connect();
      } finally {
        setBusy(false);
      }
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Connect WhatsApp</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">
          Pair this app with WhatsApp on your phone. Single-user, single-device.
        </p>
      </header>

      {isLoading && !waState ? <PanelMuted>Checking backend...</PanelMuted> : null}

      {waState?.state !== "ready" && waState?.state !== "error" ? (
        <ModeSwitch mode={mode} onChange={(m) => handleModeChange(m)} />
      ) : null}

      {waState?.state === "disconnected" && !busy && mode === "qr" ? (
        <PanelMuted>
          <div className="flex items-center justify-between gap-3">
            <span>Not connected yet.</span>
            <button
              type="button"
              onClick={() => handleManualConnect()}
              className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
            >
              Start pairing
            </button>
          </div>
        </PanelMuted>
      ) : null}

      {mode === "code" && waState?.state !== "ready" && waState?.state !== "error" ? (
        <PairCodeStarter
          phoneDraft={phoneDraft}
          setPhoneDraft={setPhoneDraft}
          err={codeErr}
          busy={busy}
          onSubmit={() => handlePairCodeConnect()}
        />
      ) : null}

      {waState?.state === "pairing" && mode === "qr" ? (
        <PairingPanel qrDataUrl={waState.qr_data_url} lastEventAt={waState.last_event_at} />
      ) : null}

      {waState?.state === "pairing" && mode === "code" ? (
        <PairCodePanel code={waState.pair_code} />
      ) : null}

      {waState?.state === "ready" ? (
        <ReadyPanel ownerPhone={waState.owner_phone} onDisconnect={() => handleDisconnect()} />
      ) : null}

      {waState?.state === "error" ? (
        <ErrorPanel message={waState.last_error} onRetry={() => handleManualConnect()} />
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

function ModeSwitch({ mode, onChange }: { mode: Mode; onChange: (m: Mode) => void }) {
  const base = "px-3 py-1.5 text-sm font-medium transition border";
  const active =
    "bg-zinc-900 dark:bg-zinc-100 text-zinc-50 dark:text-zinc-900 border-zinc-900 dark:border-zinc-100";
  const idle =
    "bg-white dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300 border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800";
  return (
    <div
      className="inline-flex rounded-md overflow-hidden"
      role="tablist"
      aria-label="Pairing mode"
    >
      <button
        type="button"
        role="tab"
        aria-selected={mode === "qr"}
        onClick={() => onChange("qr")}
        className={`${base} rounded-l-md ${mode === "qr" ? active : idle}`}
      >
        Scan QR
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={mode === "code"}
        onClick={() => onChange("code")}
        className={`${base} rounded-r-md -ml-px ${mode === "code" ? active : idle}`}
      >
        Use pair code instead
      </button>
    </div>
  );
}

function PairCodeStarter({
  phoneDraft,
  setPhoneDraft,
  err,
  busy,
  onSubmit,
}: {
  phoneDraft: string;
  setPhoneDraft: (v: string) => void;
  err: string | null;
  busy: boolean;
  onSubmit: () => void;
}) {
  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
      <h2 className="text-base font-semibold">Pair with a code</h2>
      <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
        Enter the phone number you will type the code on. WhatsApp will display "Link with phone
        number" on Linked devices.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
        className="mt-4 flex flex-wrap items-end gap-2"
      >
        <div className="flex-1 min-w-[14rem]">
          <label
            htmlFor="pair-phone"
            className="block text-xs font-medium text-zinc-700 dark:text-zinc-300"
          >
            Phone (E.164)
          </label>
          <input
            id="pair-phone"
            name="pair-phone"
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            placeholder="+919876543210"
            required
            value={phoneDraft}
            onChange={(e) => setPhoneDraft(e.target.value)}
            className="mt-1 w-full rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 text-sm font-mono"
          />
        </div>
        <button
          type="submit"
          disabled={busy || phoneDraft.trim().length === 0}
          className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {busy ? "Requesting..." : "Get pair code"}
        </button>
      </form>
      {err ? (
        <div
          role="alert"
          className="mt-3 rounded border border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950 text-red-800 dark:text-red-200 px-3 py-2 text-sm"
        >
          {err}
        </div>
      ) : null}
    </div>
  );
}

const QR_LIFETIME_S = 30;
const QR_STALE_AT_S = 20;

function PairingPanel({
  qrDataUrl,
  lastEventAt,
}: {
  qrDataUrl: string | null;
  lastEventAt: string | null;
}) {
  // Tick every 500ms so the countdown reads smoothly. SWR's 1s poll
  // bumps lastEventAt on each on_qr fire, which resets the timer.
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(id);
  }, []);

  const ageMs = useMemo(() => {
    if (!lastEventAt) return null;
    const t = Date.parse(lastEventAt);
    if (Number.isNaN(t)) return null;
    return Math.max(0, now - t);
  }, [lastEventAt, now]);
  const ageS = ageMs == null ? null : Math.floor(ageMs / 1000);
  const remainingS = ageS == null ? null : Math.max(0, QR_LIFETIME_S - ageS);

  let tone: string;
  let label: string;
  let dim = false;
  if (ageS == null || !qrDataUrl) {
    tone = "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";
    label = "Waiting for QR...";
  } else if (ageS < QR_STALE_AT_S) {
    tone = "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300";
    label = `Fresh QR. Scan within ~${remainingS}s.`;
  } else if (ageS < QR_LIFETIME_S) {
    tone = "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300";
    label = `Refreshing soon (${remainingS}s left). Wait for the next QR if your scan fails.`;
  } else {
    tone = "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300";
    label = "QR expired. Waiting for a fresh one to load...";
    dim = true;
  }

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
            className={`h-72 w-72 rounded-md border border-zinc-200 dark:border-zinc-800 bg-white p-2 transition-opacity ${dim ? "opacity-30" : "opacity-100"}`}
          />
        ) : (
          <div className="h-72 w-72 rounded-md border border-dashed border-zinc-300 dark:border-zinc-700 flex items-center justify-center text-sm text-zinc-500">
            Waiting for QR...
          </div>
        )}
      </div>
      <div
        className={`mt-3 inline-flex w-full justify-center rounded-md px-3 py-1.5 text-xs font-medium ${tone}`}
      >
        {label}
      </div>
      <p className="mt-2 text-xs text-zinc-500 text-center">
        WhatsApp rotates this code every {QR_LIFETIME_S} seconds. The page updates automatically. If
        your phone says &quot;can&apos;t connect&quot;, the QR likely expired -- wait for the next
        one.
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
  // Test-message state. The button sends a small canary to self via
  // /api/wa/test/self (backend rate-limited 15/min). Result surfaces
  // both inline and via the global toaster so the user gets feedback
  // either at the panel or wherever they're looking.
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; text: string } | null>(null);

  async function handleTestSelf() {
    setTesting(true);
    setTestResult(null);
    const ts = new Date().toISOString().replace("T", " ").slice(0, 19);
    try {
      await wa.testSelf(`Watify test message at ${ts} UTC`);
      const msg = "Test message sent. Open WhatsApp on your phone to confirm receipt.";
      setTestResult({ ok: true, text: msg });
      toast.success("Test message sent to your own number");
    } catch (e) {
      let msg = "Send failed.";
      if (e instanceof ApiError) {
        if (e.status === 409) msg = "WhatsApp is not Ready yet. Pair first.";
        else if (e.status === 429) msg = "Too many test sends. Try again in a minute.";
        else if (e.status === 403) msg = "CSRF check rejected the request.";
        else msg = `Send failed (HTTP ${e.status}).`;
      } else if (e instanceof Error) {
        msg = e.message;
      }
      setTestResult({ ok: false, text: msg });
      toast.error(msg);
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className="rounded-lg border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950 p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-emerald-900 dark:text-emerald-200">
            WhatsApp connected
          </h2>
          <p className="mt-1 text-sm text-emerald-800 dark:text-emerald-300">
            Linked as {ownerPhone ?? "this device"}.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleTestSelf}
            disabled={testing}
            className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {testing ? "Sending..." : "Test connection"}
          </button>
          <button
            type="button"
            onClick={onDisconnect}
            className="rounded-md border border-emerald-300 dark:border-emerald-800 bg-white dark:bg-zinc-900 px-3 py-1.5 text-sm font-medium text-emerald-700 dark:text-emerald-300 hover:bg-emerald-50 dark:hover:bg-zinc-800"
          >
            Disconnect
          </button>
        </div>
      </div>
      {testResult ? (
        <div
          role={testResult.ok ? "status" : "alert"}
          className={
            "mt-3 rounded border px-3 py-2 text-sm " +
            (testResult.ok
              ? "border-emerald-300 dark:border-emerald-800 bg-white dark:bg-emerald-900 text-emerald-900 dark:text-emerald-100"
              : "border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950 text-red-800 dark:text-red-200")
          }
        >
          {testResult.text}
        </div>
      ) : null}
    </div>
  );
}

function ErrorPanel({ message, onRetry }: { message: string | null; onRetry: () => void }) {
  return (
    <div className="rounded-lg border border-rose-200 dark:border-rose-900 bg-rose-50 dark:bg-rose-950 p-6">
      <h2 className="text-base font-semibold text-rose-900 dark:text-rose-200">Pairing failed</h2>
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
