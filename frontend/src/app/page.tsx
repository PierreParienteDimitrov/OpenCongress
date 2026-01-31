import Link from "next/link";
import { routes } from "@/lib/routes";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-zinc-950">
      <main className="flex min-h-screen w-full max-w-4xl flex-col items-center gap-16 py-16 px-8">
        <header className="flex flex-col items-center gap-4 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-5xl">
            OpenCongress
          </h1>
          <p className="max-w-xl text-lg text-zinc-600 dark:text-zinc-400">
            Track congressional activity, explore legislation, and follow your representatives.
          </p>
        </header>

        <nav className="grid w-full gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <Link
            href={routes.thisWeek.index}
            className="group flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-6 transition-all hover:border-zinc-300 hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">📰</span>
              <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                This Week
              </h2>
            </div>
            <p className="text-zinc-600 dark:text-zinc-400">
              AI-generated summaries of the week in review and the week ahead in Congress.
            </p>
            <span className="mt-auto text-sm font-medium text-blue-600 group-hover:underline dark:text-blue-400">
              Read Summary →
            </span>
          </Link>

          <Link
            href={routes.calendar.index}
            className="group flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-6 transition-all hover:border-zinc-300 hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">📅</span>
              <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                Legislative Calendar
              </h2>
            </div>
            <p className="text-zinc-600 dark:text-zinc-400">
              View upcoming and past votes, bills, and congressional activity by week.
            </p>
            <span className="mt-auto text-sm font-medium text-blue-600 group-hover:underline dark:text-blue-400">
              View Calendar →
            </span>
          </Link>

          <Link
            href={routes.senator.index}
            className="group flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-6 transition-all hover:border-zinc-300 hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">🏛️</span>
              <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                Senators
              </h2>
            </div>
            <p className="text-zinc-600 dark:text-zinc-400">
              Explore senator profiles, voting records, and sponsored legislation.
            </p>
            <span className="mt-auto text-sm font-medium text-blue-600 group-hover:underline dark:text-blue-400">
              Browse Senators →
            </span>
          </Link>

          <Link
            href={routes.representative.index}
            className="group flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-6 transition-all hover:border-zinc-300 hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">🏠</span>
              <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                Representatives
              </h2>
            </div>
            <p className="text-zinc-600 dark:text-zinc-400">
              Explore representative profiles, voting records, and sponsored legislation.
            </p>
            <span className="mt-auto text-sm font-medium text-blue-600 group-hover:underline dark:text-blue-400">
              Browse Representatives →
            </span>
          </Link>
        </nav>

        <footer className="mt-auto text-center text-sm text-zinc-500 dark:text-zinc-500">
          Making congressional data accessible and transparent.
        </footer>
      </main>
    </div>
  );
}
