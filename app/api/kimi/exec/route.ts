import { NextResponse } from "next/server";

const KIMI_CLI_URL = process.env.KIMI_CLI_URL || "http://kimi-cli-a5jcf4:8000";
const KIMI_API_KEY = process.env.KIMI_API_KEY || "kimi-service-secret-key-2024";

export async function POST(req: Request) {
  try {
    const { command, cwd } = await req.json();
    
    if (!command) {
      return NextResponse.json(
        { error: "Comando requerido" },
        { status: 400 }
      );
    }

    const response = await fetch(`${KIMI_CLI_URL}/execute`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": KIMI_API_KEY,
      },
      body: JSON.stringify({
        user_id: "default-user",
        command,
        cwd,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Error del servicio Kimi: ${errorText}` },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Error executing command:", error);
    return NextResponse.json(
      { error: "Error al ejecutar comando" },
      { status: 500 }
    );
  }
}
