import Link from "next/link";

// TKT-0027 / TKT-0028: dashboard moved from `/` to `/dashboard` so `/`
// can be the public hero. TopNav still hardwires links here; TKT-0028
// will swap this for an auth-aware nav.
const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/connect", label: "Connect" },
  { href: "/groups", label: "Groups" },
  { href: "/send", label: "Send" },
  { href: "/history", label: "History" },
];

export default function TopNav() {
  return (
    <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/80 backdrop-blur">
      <nav className="mx-auto max-w-6xl flex items-center gap-1 px-4 h-14">
        <Link
          href="/"
          className="text-base font-semibold tracking-tight mr-4"
        >
          Watify
        </Link>
        <ul className="flex items-center gap-1 text-sm">
          {links.slice(1).map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                className="px-3 py-1.5 rounded-md text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-900 transition"
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
