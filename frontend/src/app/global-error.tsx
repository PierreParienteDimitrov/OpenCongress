"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

export default function GlobalError({
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
    <html lang="en">
      <body
        style={{
          backgroundColor: "#1a1a2e",
          color: "#f5f5f5",
          fontFamily: "system-ui, sans-serif",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100vh",
          textAlign: "center",
          padding: "2rem",
        }}
      >
        <h1 style={{ fontSize: "1.5rem", fontWeight: "bold" }}>
          Something went wrong
        </h1>
        <p
          style={{ marginTop: "0.5rem", color: "#a0a0a0", maxWidth: "28rem" }}
        >
          A critical error occurred. Our team has been notified.
        </p>
        {error.digest && (
          <p
            style={{
              marginTop: "0.25rem",
              fontSize: "0.75rem",
              color: "#666",
              fontFamily: "monospace",
            }}
          >
            Error ID: {error.digest}
          </p>
        )}
        <button
          onClick={reset}
          style={{
            marginTop: "1.5rem",
            padding: "0.5rem 1.5rem",
            backgroundColor: "#4a6fa5",
            color: "#fff",
            border: "none",
            borderRadius: "0.25rem",
            cursor: "pointer",
            fontSize: "0.875rem",
            fontWeight: 500,
          }}
        >
          Try Again
        </button>
      </body>
    </html>
  );
}
