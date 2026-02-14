import Link from "next/link";
import { GridContainer } from "@/components/layout/GridContainer";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="min-h-[60vh] bg-background">
      <GridContainer className="flex flex-col items-center justify-center py-20 text-center">
        <p className="text-6xl font-bold text-muted-foreground/30">404</p>
        <h1 className="mt-4 text-2xl font-bold text-foreground">
          Page Not Found
        </h1>
        <p className="mt-2 max-w-md text-sm text-muted-foreground">
          The page you are looking for does not exist or has been moved.
        </p>
        <div className="mt-6">
          <Button asChild className="cursor-pointer">
            <Link href="/">Back to OpenCongress</Link>
          </Button>
        </div>
      </GridContainer>
    </main>
  );
}
