import { NextResponse } from "next/server";

const KIMI_CLI_URL = process.env.KIMI_CLI_URL || "http://kimi-cli-a5jcf4:8000";
const KIMI_API_KEY = process.env.KIMI_API_KEY || "kimi-service-secret-key-2024";

export async function POST(req: Request) {
  try {
    const { repoUrl, repoName, userId } = await req.json();
    
    if (!repoUrl || !repoName) {
      return NextResponse.json(
        { error: "repoUrl y repoName son requeridos" },
        { status: 400 }
      );
    }

    const response = await fetch(`${KIMI_CLI_URL}/workspace/init`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": KIMI_API_KEY,
      },
      body: JSON.stringify({
        user_id: userId || "default",
        repo_url: repoUrl,
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
    return NextResponse.json({
      success: true,
      message: "Repositorio clonado exitosamente",
      workspace_dir: result.workspace_dir,
      repo_name: repoName,
      clone_result: result,
    });
  } catch (error) {
    console.error("Error cloning repo:", error);
    return NextResponse.json(
      { error: "Error al clonar repositorio" },
      { status: 500 }
    );
  }
}
