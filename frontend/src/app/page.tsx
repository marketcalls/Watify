import HeroCTAs from "@/components/HeroCTAs";

export const metadata = {
  title: "Watify -- WhatsApp notifications for your friend watchlists",
  description:
    "Single-user WhatsApp notification service. Pair with QR, group your contacts, send on schedule with a random per-recipient delay.",
};

// TKT-0044 iter B: Supabase-style hero. Pitch-black surface (already
// set on <body> via the dark default + globals.css surface-0 token),
// subtle grid overlay, top pill badge with pulse dot, two-line
// gradient headline, stat row, brand CTAs + GitHub link, integrates-
// with chip row.

export default function HeroPage() {
  return (
    <div className="relative space-y-16">
      {/* TKT-0044: subtle grid backdrop. Faded by mask-image so it
          never competes with the foreground text. Sits behind the
          hero content via z-index. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 opacity-30 dark:opacity-40 [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_70%)]"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(127,127,127,0.15) 1px, transparent 1px), linear-gradient(to bottom, rgba(127,127,127,0.15) 1px, transparent 1px)",
          backgroundSize: "44px 44px",
        }}
      />

      <section className="pt-12 pb-4 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-zinc-300 dark:border-zinc-800 bg-white/60 dark:bg-zinc-900/60 backdrop-blur px-3 py-1 text-xs font-medium text-zinc-700 dark:text-zinc-300">
          <span className="relative inline-flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          <span className="uppercase tracking-wider">Single-user WhatsApp notifications</span>
        </div>

        <h1 className="mt-6 text-4xl sm:text-6xl font-semibold tracking-tight leading-[1.05]">
          <span className="block text-zinc-900 dark:text-white">Send WhatsApp to your</span>
          <span className="block bg-gradient-to-r from-emerald-300 via-teal-300 to-cyan-300 bg-clip-text text-transparent">
            friend watchlists
          </span>
        </h1>

        <p className="mt-6 max-w-2xl mx-auto text-base sm:text-lg text-zinc-600 dark:text-zinc-400">
          A notification service you run on your own host. Pair once with WhatsApp, organize
          contacts into watchlists, and send messages now or on a schedule.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <HeroCTAs />
          <a
            href="https://github.com/marketcalls/Watify"
            target="_blank"
            rel="noreferrer"
            className="rounded-md border border-zinc-300 dark:border-zinc-700 px-5 py-2.5 text-sm font-medium text-zinc-800 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-900"
          >
            GitHub
          </a>
        </div>
      </section>

      <section>
        <p className="text-center text-xs uppercase tracking-widest text-zinc-500 dark:text-zinc-400">
          Built with
        </p>
        <div className="mt-3 flex flex-wrap justify-center gap-2 text-sm">
          <Chip>WhatsApp</Chip>
          <Chip>SQLite</Chip>
          <Chip>APScheduler</Chip>
          <Chip>FastAPI</Chip>
          <Chip>Next.js</Chip>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <FeatureCard
          title="Pair with QR or pair-code"
          body="Scan the QR from your phone or use a pair-code. One device, one host, file-backed session that survives restarts."
        />
        <FeatureCard
          title="Organize contacts into watchlists"
          body="Add contacts one at a time or bulk-paste in CSV form. Deduplication on phone number is automatic."
        />
        <FeatureCard
          title="Send now or schedule"
          body="Compose once, dispatch immediately or schedule for later. Full attempt history, per-recipient retry detail."
        />
      </section>

      <footer className="border-t border-zinc-200 dark:border-zinc-800 pt-6 text-xs text-zinc-500 dark:text-zinc-400">
        Watify is single-user. Built on the unofficial wars library; see
        <code className="mx-1 rounded bg-zinc-100 dark:bg-zinc-900 px-1 py-0.5">docs/wars.md</code>
        for risk notes.
      </footer>
    </div>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-white">
        {value}
      </span>
      <span className="text-xs uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
        {label}
      </span>
    </div>
  );
}

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full border border-zinc-300 dark:border-zinc-800 bg-white/60 dark:bg-zinc-900/60 px-3 py-1 font-mono text-xs text-zinc-700 dark:text-zinc-300">
      {children}
    </span>
  );
}

function FeatureCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/60 p-5">
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">{body}</p>
    </div>
  );
}
