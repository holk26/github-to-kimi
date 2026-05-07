import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";

const KIMI_CLI_URL = process.env.KIMI_CLI_URL || "http://kimi-cli:8000";

export async function POST(req: Request) {
  try {
    const session = await getServerSession();
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: "No autorizado" }, { status: 401 });
    }

    const { repo_url, repo_name } = await req.json();

    if (!repo_url || !repo_name) {
      return NextResponse.json(
        { error: "URL y nombre del repo requeridos" },
        { status: 400 }
      );
    }

    await fetch(`${KIMI_CLI_URL}/workspace/init`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: session.user.id }),
    });

    const response = await fetch(`${KIMI_CLI_URL}/repo/clone`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: session.user.id,
        repo_url,
        repo_name,
      }),
    });

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Error cloning repo:", error);
    return NextResponse.json(
      { error: "Error al clonar repositorio" },
      { status: 500 }
    );
  }
}
