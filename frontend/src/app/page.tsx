import Link from "next/link";
import { routes } from "@/lib/routes";
import { GridContainer } from "@/components/layout/GridContainer";
import { ChatContextProvider } from "@/lib/chat-context";
import { Card } from "@/components/ui/card";

export default function Home() {
  return (
    <ChatContextProvider context={{ type: "home", data: {} }}>
    <div className="flex min-h-[calc(100vh-var(--navbar-height))] items-center justify-center bg-background font-sans">
      <GridContainer className="flex flex-col items-center gap-16 py-16">
        <header className="flex flex-col items-center gap-4 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
            OpenCongress
          </h1>
          <p className="max-w-xl text-lg text-muted-foreground">
            Track congressional activity, explore legislation, and follow your representatives.
          </p>
        </header>

        <nav className="grid w-full gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <Link href={routes.thisWeek.index} className="group">
            <Card className="flex h-full flex-col gap-3 p-6 py-6 transition-all hover:border-muted-foreground/30 hover:shadow-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">📰</span>
                <h2 className="text-xl font-semibold text-foreground">
                  This Week
                </h2>
              </div>
              <p className="text-muted-foreground">
                AI-generated summaries of the week in review and the week ahead in Congress.
              </p>
              <span className="mt-auto text-sm font-medium text-accent group-hover:underline">
                Read Summary →
              </span>
            </Card>
          </Link>

          <Link href={routes.calendar.index} className="group">
            <Card className="flex h-full flex-col gap-3 p-6 py-6 transition-all hover:border-muted-foreground/30 hover:shadow-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">📅</span>
                <h2 className="text-xl font-semibold text-foreground">
                  Legislative Calendar
                </h2>
              </div>
              <p className="text-muted-foreground">
                View upcoming and past votes, bills, and congressional activity by week.
              </p>
              <span className="mt-auto text-sm font-medium text-accent group-hover:underline">
                View Calendar →
              </span>
            </Card>
          </Link>

          <Link href={routes.senate.index} className="group">
            <Card className="flex h-full flex-col gap-3 p-6 py-6 transition-all hover:border-muted-foreground/30 hover:shadow-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🏛️</span>
                <h2 className="text-xl font-semibold text-foreground">
                  Senate
                </h2>
              </div>
              <p className="text-muted-foreground">
                Explore the 100 U.S. Senate seats, state map, and senator profiles.
              </p>
              <span className="mt-auto text-sm font-medium text-accent group-hover:underline">
                Explore Senate →
              </span>
            </Card>
          </Link>

          <Link href={routes.house.index} className="group">
            <Card className="flex h-full flex-col gap-3 p-6 py-6 transition-all hover:border-muted-foreground/30 hover:shadow-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🏠</span>
                <h2 className="text-xl font-semibold text-foreground">
                  House
                </h2>
              </div>
              <p className="text-muted-foreground">
                Explore the 435 U.S. House seats, district map, and representative profiles.
              </p>
              <span className="mt-auto text-sm font-medium text-accent group-hover:underline">
                Explore House →
              </span>
            </Card>
          </Link>

          <Link href={routes.documentation.index} className="group">
            <Card className="flex h-full flex-col gap-3 p-6 py-6 transition-all hover:border-muted-foreground/30 hover:shadow-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">📖</span>
                <h2 className="text-xl font-semibold text-foreground">
                  Documentation
                </h2>
              </div>
              <p className="text-muted-foreground">
                Learn how OpenCongress works, our data sources, and technology.
              </p>
              <span className="mt-auto text-sm font-medium text-accent group-hover:underline">
                Learn More →
              </span>
            </Card>
          </Link>
        </nav>

        <footer className="mt-auto text-center text-sm text-muted-foreground">
          Making congressional data accessible and transparent.
        </footer>
      </GridContainer>
    </div>
    </ChatContextProvider>
  );
}
