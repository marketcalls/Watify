"use client";

import { useMemo } from "react";
import BackendStatus from "@/components/BackendStatus";
import SoftCapBanner from "@/components/SoftCapBanner";
import WhatsAppTile from "@/components/WhatsAppTile";
import { useGroups } from "@/hooks/useGroups";
import { useJobs } from "@/hooks/useJobs";

export default function DashboardPage() {
  const { list: groups } = useGroups();
  const { list: jobs } = useJobs();

  const { stats, sent24h } = useMemo(() => {
    const totalContacts = groups.reduce(
      (s, g) => s + (g.contact_count ?? 0),
      0
    );
    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);
    const cutoff24h = Date.now() - 24 * 60 * 60 * 1000;

    let jobsToday = 0;
    let sent24hCount = 0;
    for (const j of jobs) {
      const created = new Date(j.created_at).getTime();
      if (created >= startOfDay.getTime()) jobsToday++;
      if (created >= cutoff24h) sent24hCount += j.counts?.sent ?? 0;
    }
    return {
      sent24h: sent24hCount,
      stats: [
        { label: "Friend groups", value: String(groups.length) },
        { label: "Contacts", value: String(totalContacts) },
        { label: "Jobs today", value: String(jobsToday) },
        { label: "Sent (24h)", value: String(sent24hCount) },
      ],
    };
  }, [groups, jobs]);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">
            WhatsApp notifications for your friend watchlists.
          </p>
        </div>
        <BackendStatus />
      </header>

      <SoftCapBanner sent24h={sent24h} />

      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <WhatsAppTile />
        {stats.map((s) => (
          <div
            key={s.label}
            className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-4"
          >
            <div className="text-xs uppercase tracking-wide text-zinc-500">
              {s.label}
            </div>
            <div className="mt-1 text-lg font-medium">{s.value}</div>
          </div>
        ))}
      </section>

      <section className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
        <h2 className="text-base font-semibold">Getting started</h2>
        <ol className="mt-3 list-decimal pl-5 text-sm space-y-1 text-zinc-700 dark:text-zinc-300">
          <li>Open Connect and scan the QR with WhatsApp on your phone.</li>
          <li>Create a friend group with up to 20 contacts.</li>
          <li>Compose a message on Send and dispatch immediately or schedule it.</li>
        </ol>
      </section>
    </div>
  );
}
