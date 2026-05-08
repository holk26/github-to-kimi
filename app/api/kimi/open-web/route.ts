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

    // 1. First, ensure the repo is cloned in the workspace
    const initResponse = await fetch(`${KIMI_CLI_URL}/workspace/init`, {
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

    if (!initResponse.ok) {
      const errorText = await initResponse.text();
      return NextResponse.json(
        { error: `Error del servicio Kimi: ${errorText}` },
        { status: initResponse.status }
      );
    }

    // 2. Call the kimi-web/open endpoint to get the URL
    const openResponse = await fetch(`${KIMI_CLI_URL}/kimi-web/open`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": KIMI_API_KEY,
      },
      body: JSON.stringify({
        user_id: userId || "default",
        repo_url: repoUrl,
        repo_name: repoName,
      }),
    });

    if (!openResponse.ok) {
      const errorText = await openResponse.text();
      return NextResponse.json(
        { error: `Error al abrir Kimi Web: ${errorText}` },
        { status: openResponse.status }
      );
    }

    const result = await openResponse.json();

    return NextResponse.json({
      success: true,
      message: "Kimi Web preparado exitosamente",
      kimi_web_url: result.kimi_web_url,
      repo_name: repoName,
      project_dir: result.project_dir,
    });
  } catch (error) {
    console.error("Error opening Kimi Web:", error);
    return NextResponse.json(
      { error: "Error al abrir Kimi Web" },
      { status: 500 }
    );
  }
}
