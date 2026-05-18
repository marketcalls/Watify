import BackendStatus from "@/components/BackendStatus";
import WhatsAppTile from "@/components/WhatsAppTile";

export default function DashboardPage() {
  const stats = [
    { label: "Friend groups", value: "0" },
    { label: "Contacts", value: "0" },
    { label: "Jobs today", value: "0" },
  ];

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

      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
