"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  ApiError,
  DEFAULT_MAX_DELAY_S,
  DEFAULT_MIN_DELAY_S,
  MAX_DELAY_S,
  type SendJobRead,
} from "@/lib/api";
import { useGroups } from "@/hooks/useGroups";
import { useJobs } from "@/hooks/useJobs";

type Mode = "now" | "schedule";

function nowLocalIsoForInput(): string {
  // Returns "YYYY-MM-DDTHH:MM" suitable for <input type="datetime-local">,
  // in the user's local timezone, rounded up to the next minute.
  const d = new Date(Date.now() + 60_000);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`;
}

export default function SendPage() {
  const { list: groups, isLoading: groupsLoading } = useGroups();
  const { createSend } = useJobs();

  const [groupId, setGroupId] = useState<number | "">("");
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState<Mode>("now");
  const [scheduleAt, setScheduleAt] = useState(nowLocalIsoForInput);
  const [minDelay, setMinDelay] = useState(DEFAULT_MIN_DELAY_S);
  const [maxDelay, setMaxDelay] = useState(DEFAULT_MAX_DELAY_S);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<SendJobRead | null>(null);

  useEffect(() => {
    if (groupId === "" && groups.length > 0) {
      setGroupId(groups[0].id);
    }
  }, [groups, groupId]);

  const selectedGroup = useMemo(
    () => groups.find((g) => g.id === groupId) ?? null,
    [groups, groupId]
  );

  const rangeError =
    minDelay > maxDelay ? "Min delay must be <= max delay." : null;
  const canSubmit =
    !submitting &&
    selectedGroup != null &&
    selectedGroup.contact_count > 0 &&
    message.trim().length > 0 &&
    rangeError == null &&
    minDelay >= 1 &&
    maxDelay <= MAX_DELAY_S;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit || selectedGroup == null) return;
    setError(null);
    setCreated(null);
    setSubmitting(true);
    try {
      const schedule =
        mode === "now"
          ? "now"
          : // Convert local datetime input into a tz-aware ISO string.
            new Date(scheduleAt).toISOString();
      const job = await createSend({
        group_id: selectedGroup.id,
        message: message.trim(),
        schedule,
        min_delay_s: minDelay,
        max_delay_s: maxDelay,
      });
      setCreated(job);
      setMessage("");
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.status === 409) setError("Backend not ready or job already terminal.");
        else if (e.status === 422)
          setError(
            typeof e.body === "object" && e.body && "detail" in e.body
              ? String((e.body as { detail: unknown }).detail)
              : "Invalid input. Check delay range and schedule."
          );
        else setError(e.message);
      } else {
        setError("Could not create the send job.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Send Message</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">
          Compose a message and dispatch immediately or schedule for later.
        </p>
      </header>

      <form
        onSubmit={onSubmit}
        className="space-y-5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5"
      >
        <div className="space-y-1">
          <label className="block text-xs uppercase tracking-wide text-zinc-500">
            Group
          </label>
          {groupsLoading && groups.length === 0 ? (
            <p className="text-sm text-zinc-500">Loading groups...</p>
          ) : groups.length === 0 ? (
            <p className="text-sm text-zinc-500">
              No groups yet.{" "}
              <Link href="/groups" className="text-emerald-700 hover:underline">
                Create one first
              </Link>
              .
            </p>
          ) : (
            <select
              value={groupId === "" ? "" : String(groupId)}
              onChange={(e) =>
                setGroupId(e.target.value === "" ? "" : Number(e.target.value))
              }
              className="w-full rounded-md border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-2 py-1.5 text-sm"
            >
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name} ({g.contact_count} contact
                  {g.contact_count === 1 ? "" : "s"})
                </option>
              ))}
            </select>
          )}
          {selectedGroup != null && selectedGroup.contact_count === 0 && (
            <p className="text-xs text-rose-600">
              This group has no contacts yet. Add at least one in{" "}
              <Link href="/groups" className="underline">
                Groups
              </Link>
              .
            </p>
          )}
        </div>

        <div className="space-y-1">
          <label className="block text-xs uppercase tracking-wide text-zinc-500">
            Message
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={5}
            maxLength={4096}
            placeholder="Type the message you want to broadcast..."
            className="w-full rounded-md border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2 text-sm font-mono"
          />
          <div className="text-xs text-zinc-500 text-right">
            {message.length} / 4096
          </div>
        </div>

        <div className="space-y-2">
          <label className="block text-xs uppercase tracking-wide text-zinc-500">
            When
          </label>
          <div className="flex items-center gap-3">
            <ModeButton
              active={mode === "now"}
              onClick={() => setMode("now")}
              label="Send Now"
            />
            <ModeButton
              active={mode === "schedule"}
              onClick={() => setMode("schedule")}
              label="Schedule"
            />
          </div>
          {mode === "schedule" && (
            <input
              type="datetime-local"
              value={scheduleAt}
              onChange={(e) => setScheduleAt(e.target.value)}
              className="rounded-md border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-2 py-1.5 text-sm"
            />
          )}
        </div>

        <div className="space-y-1">
          <label className="block text-xs uppercase tracking-wide text-zinc-500">
            Per-recipient delay (seconds)
          </label>
          <div className="flex items-center gap-2">
            <NumberField
              label="Min"
              value={minDelay}
              onChange={setMinDelay}
              min={1}
              max={MAX_DELAY_S}
            />
            <span className="text-zinc-500">to</span>
            <NumberField
              label="Max"
              value={maxDelay}
              onChange={setMaxDelay}
              min={1}
              max={MAX_DELAY_S}
            />
          </div>
          <p className="text-xs text-zinc-500">
            Each recipient gets a random delay between {minDelay} and {maxDelay}{" "}
            seconds before its send. One message at a time.
          </p>
          {rangeError && (
            <p className="text-xs text-rose-600">{rangeError}</p>
          )}
        </div>

        {error && (
          <div className="rounded-md border border-rose-200 dark:border-rose-900 bg-rose-50 dark:bg-rose-950 p-3 text-xs text-rose-700 dark:text-rose-300">
            {error}
          </div>
        )}

        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-zinc-500">
            {selectedGroup
              ? `Will dispatch to ${selectedGroup.contact_count} contact${
                  selectedGroup.contact_count === 1 ? "" : "s"
                } in "${selectedGroup.name}".`
              : "Pick a group above."}
          </p>
          <button
            type="submit"
            disabled={!canSubmit}
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:bg-zinc-300 dark:disabled:bg-zinc-700 disabled:cursor-not-allowed"
          >
            {submitting
              ? "Submitting..."
              : mode === "now"
                ? "Send Now"
                : "Schedule send"}
          </button>
        </div>
      </form>

      {created && (
        <div className="rounded-lg border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950 p-5 text-sm text-emerald-800 dark:text-emerald-300">
          <p>
            Job <span className="font-mono">#{created.id}</span> queued (status:{" "}
            <span className="font-medium">{created.status}</span>).
          </p>
          <p className="mt-1">
            <Link
              href="/history"
              className="underline text-emerald-700 dark:text-emerald-300"
            >
              View in History
            </Link>
          </p>
        </div>
      )}
    </div>
  );
}

function ModeButton({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-md px-3 py-1.5 text-sm font-medium border transition ${
        active
          ? "bg-emerald-600 text-white border-emerald-600"
          : "bg-white dark:bg-zinc-950 text-zinc-700 dark:text-zinc-300 border-zinc-300 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800"
      }`}
    >
      {label}
    </button>
  );
}

function NumberField({
  label,
  value,
  onChange,
  min,
  max,
}: {
  label: string;
  value: number;
  onChange: (n: number) => void;
  min: number;
  max: number;
}) {
  return (
    <label className="flex items-center gap-1">
      <span className="text-xs text-zinc-500">{label}</span>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        onChange={(e) => {
          const n = Number(e.target.value);
          if (Number.isFinite(n)) onChange(Math.min(max, Math.max(min, n)));
        }}
        className="w-20 rounded-md border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-2 py-1.5 text-sm"
      />
    </label>
  );
}
