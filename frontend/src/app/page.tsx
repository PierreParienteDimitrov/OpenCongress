import Link from "next/link";
import { routes } from "@/lib/routes";
import { GridContainer } from "@/components/layout/GridContainer";
import { Card } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background font-sans">
      <GridContainer className="flex min-h-screen flex-col items-center gap-16 py-16">
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

          <Link href={routes.senator.index} className="group">
            <Card className="flex h-full flex-col gap-3 p-6 py-6 transition-all hover:border-muted-foreground/30 hover:shadow-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🏛️</span>
                <h2 className="text-xl font-semibold text-foreground">
                  Senators
                </h2>
              </div>
              <p className="text-muted-foreground">
                Explore senator profiles, voting records, and sponsored legislation.
              </p>
              <span className="mt-auto text-sm font-medium text-accent group-hover:underline">
                Browse Senators →
              </span>
            </Card>
          </Link>

          <Link href={routes.representative.index} className="group">
            <Card className="flex h-full flex-col gap-3 p-6 py-6 transition-all hover:border-muted-foreground/30 hover:shadow-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🏠</span>
                <h2 className="text-xl font-semibold text-foreground">
                  Representatives
                </h2>
              </div>
              <p className="text-muted-foreground">
                Explore representative profiles, voting records, and sponsored legislation.
              </p>
              <span className="mt-auto text-sm font-medium text-accent group-hover:underline">
                Browse Representatives →
              </span>
            </Card>
          </Link>

          <Link href={routes.senateSeats.index} className="group">
            <Card className="flex h-full flex-col gap-3 p-6 py-6 transition-all hover:border-muted-foreground/30 hover:shadow-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🏛️</span>
                <h2 className="text-xl font-semibold text-foreground">
                  Senate Seat Map
                </h2>
              </div>
              <p className="text-muted-foreground">
                Interactive hemicycle visualization of U.S. Senate seats with vote overlay.
              </p>
              <span className="mt-auto text-sm font-medium text-accent group-hover:underline">
                View Senate Map →
              </span>
            </Card>
          </Link>

          <Link href={routes.houseSeats.index} className="group">
            <Card className="flex h-full flex-col gap-3 p-6 py-6 transition-all hover:border-muted-foreground/30 hover:shadow-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🏠</span>
                <h2 className="text-xl font-semibold text-foreground">
                  House Seat Map
                </h2>
              </div>
              <p className="text-muted-foreground">
                Interactive hemicycle visualization of U.S. House seats with vote overlay.
              </p>
              <span className="mt-auto text-sm font-medium text-accent group-hover:underline">
                View House Map →
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
  );
}
