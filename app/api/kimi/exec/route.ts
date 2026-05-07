import { NextResponse } from "next/server";

const KIMI_CLI_URL = process.env.KIMI_CLI_URL || "http://kimi-cli-a5jcf4:8000";

export async function POST(req: Request) {
  try {
    const { command } = await req.json();

    if (!command) {
      return NextResponse.json({ error: "Comando requerido" }, { status: 400 });
    }

    // Primero verificar health del servicio
    try {
      const healthResponse = await fetch(`${KIMI_CLI_URL}/health`, {
        method: "GET",
      });
      const healthData = await healthResponse.json();
      console.log("Kimi CLI health:", healthData);
    } catch (healthError) {
      console.error("Kimi CLI health check failed:", healthError);
    }

    const response = await fetch(`${KIMI_CLI_URL}/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "default-user",
        command,
      }),
    });

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Error executing command:", error);
    return NextResponse.json(
      { error: "Error al ejecutar comando", details: String(error) },
      { status: 500 }
    );
  }
}
