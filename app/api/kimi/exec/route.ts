import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";

const KIMI_CLI_URL = process.env.KIMI_CLI_URL || "http://kimi-cli:8000";

export async function POST(req: Request) {
  try {
    const session = await getServerSession();
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: "No autorizado" }, { status: 401 });
    }

    const { command, cwd, env } = await req.json();

    if (!command) {
      return NextResponse.json(
        { error: "Comando requerido" },
        { status: 400 }
      );
    }

    const response = await fetch(`${KIMI_CLI_URL}/exec`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: session.user.id,
        command,
        cwd,
        env,
      }),
    });

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
