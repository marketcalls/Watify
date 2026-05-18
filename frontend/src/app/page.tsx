import Link from "next/link";

export const metadata = {
  title: "Watify -- WhatsApp notifications for your friend watchlists",
  description:
    "Single-user WhatsApp notification service. Pair with QR, group your contacts, send on schedule with a random per-recipient delay.",
};

export default function HeroPage() {
  return (
    <div className="space-y-16">
      <section className="pt-8 pb-4">
        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight leading-tight">
          Send WhatsApp messages to your friend watchlists -- on your own terms.
        </h1>
        <p className="mt-5 max-w-2xl text-base sm:text-lg text-zinc-600 dark:text-zinc-400">
          Watify is a single-user WhatsApp notification service you run on your own
          host. Pair once with QR, group contacts into watchlists capped at 20, and
          send right now or on a schedule with a random delay between each recipient.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/login"
            className="rounded bg-zinc-900 dark:bg-zinc-100 text-zinc-50 dark:text-zinc-900 px-5 py-2.5 text-sm font-medium"
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className="rounded border border-zinc-300 dark:border-zinc-700 px-5 py-2.5 text-sm font-medium hover:bg-zinc-100 dark:hover:bg-zinc-900"
          >
            Get started
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <FeatureCard
          title="Pair with QR or pair-code"
          body="Scan the QR from your phone or use a pair-code -- one device, one host, file-backed session that survives restarts."
        />
        <FeatureCard
          title="Friend groups, capped at 20"
          body="Bulk-add contacts in groups of up to 20. Every send fires with a configurable random delay of 3 to 30 seconds between recipients to keep behaviour conversational."
        />
        <FeatureCard
          title="Send now or schedule"
          body="Compose once, dispatch immediately or schedule for later. One message at a time, full attempt history, per-recipient retry detail."
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

function FeatureCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5">
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">{body}</p>
    </div>
  );
}
