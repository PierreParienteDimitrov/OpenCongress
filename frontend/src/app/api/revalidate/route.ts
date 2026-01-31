import { revalidatePath } from "next/cache";
import { NextRequest, NextResponse } from "next/server";

/**
 * ISR Revalidation endpoint.
 * Called by the backend to trigger on-demand revalidation of cached pages.
 *
 * POST /api/revalidate
 * Body: { path: string, secret: string }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { path, secret } = body;

    // Validate secret
    const expectedSecret = process.env.REVALIDATION_SECRET;
    if (!expectedSecret) {
      console.error("REVALIDATION_SECRET not configured");
      return NextResponse.json(
        { error: "Server configuration error" },
        { status: 500 }
      );
    }

    if (secret !== expectedSecret) {
      return NextResponse.json({ error: "Invalid secret" }, { status: 401 });
    }

    // Validate path
    if (!path || typeof path !== "string") {
      return NextResponse.json(
        { error: "Missing or invalid path" },
        { status: 400 }
      );
    }

    // Ensure path starts with /
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;

    // Revalidate the path
    revalidatePath(normalizedPath);

    console.log(`Revalidated path: ${normalizedPath}`);

    return NextResponse.json({
      revalidated: true,
      path: normalizedPath,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Revalidation error:", error);
    return NextResponse.json(
      { error: "Failed to revalidate" },
      { status: 500 }
    );
  }
}
