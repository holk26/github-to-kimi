import { NextResponse } from "next/server";

const KIMI_CLI_URL = process.env.KIMI_CLI_URL || "http://kimi-cli-a5jcf4:8000";

export async function POST(req: Request) {
  try {
    const { repoUrl, repoName, userId = "default-user" } = await req.json();

    if (!repoUrl || !repoName) {
      return NextResponse.json(
        { error: "repoUrl y repoName son requeridos" },
        { status: 400 }
      );
    }

    // 1. Inicializar el workspace del usuario
    const initResponse = await fetch(`${KIMI_CLI_URL}/workspace/init`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        repo_url: repoUrl,
      }),
    });

    const initResult = await initResponse.json();

    // 2. Si el clone falló o el repo ya existía, hacer git pull
    if (initResult.clone_returncode !== 0) {
      // Intentar hacer git pull en el directorio existente
      const pullResponse = await fetch(`${KIMI_CLI_URL}/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          command: `cd ${repoName} && git pull`,
        }),
      });
      const pullResult = await pullResponse.json();
      
      return NextResponse.json({
        success: true,
        message: "Repositorio actualizado",
        workspace_dir: initResult.workspace_dir,
        repo_name: repoName,
        clone_result: initResult,
        pull_result: pullResult,
      });
    }

    return NextResponse.json({
      success: true,
      message: "Repositorio clonado exitosamente",
      workspace_dir: initResult.workspace_dir,
      repo_name: repoName,
      clone_result: initResult,
    });
  } catch (error) {
    console.error("Error cloning repo:", error);
    return NextResponse.json(
      { error: "Error al clonar el repositorio", details: String(error) },
      { status: 500 }
    );
  }
}
