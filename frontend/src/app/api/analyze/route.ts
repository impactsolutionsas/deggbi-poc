import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    // Relayer le body brut avec le content-type original (multipart/form-data avec boundary)
    const contentType = request.headers.get("content-type") || "";
    const body = await request.arrayBuffer();

    const resp = await fetch(`${BACKEND_URL}/api/v1/test/analyze`, {
      method: "POST",
      headers: { "Content-Type": contentType },
      body: body,
    });

    const text = await resp.text();
    try {
      const data = JSON.parse(text);
      return NextResponse.json(data, { status: resp.status });
    } catch {
      return NextResponse.json(
        { detail: `Backend error: ${text.slice(0, 200)}` },
        { status: resp.status || 502 }
      );
    }
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : "Backend unreachable";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}
