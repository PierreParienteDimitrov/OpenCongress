"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GridContainer } from "@/components/layout/GridContainer";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <main className="min-h-[60vh] bg-background">
      <GridContainer className="flex flex-col items-center justify-center py-20 text-center">
        <AlertTriangle className="mb-4 size-12 text-destructive" />
        <h1 className="text-2xl font-bold text-foreground">
          Something went wrong
        </h1>
        <p className="mt-2 max-w-md text-sm text-muted-foreground">
          An unexpected error occurred while loading this page. Our team has
          been notified.
        </p>
        {error.digest && (
          <p className="mt-1 font-mono text-xs text-muted-foreground">
            Error ID: {error.digest}
          </p>
        )}
        <div className="mt-6 flex gap-3">
          <Button onClick={reset} className="cursor-pointer">
            Try Again
          </Button>
          <Button
            variant="outline"
            className="cursor-pointer"
            onClick={() => (window.location.href = "/")}
          >
            Go Home
          </Button>
        </div>
      </GridContainer>
    </main>
  );
}
