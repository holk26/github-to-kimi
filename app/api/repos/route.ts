import { NextResponse } from "next/server";

export interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  clone_url: string;
  ssh_url: string;
  stargazers_count: number;
  language: string | null;
  forks_count: number;
  updated_at: string;
  private: boolean;
  owner: {
    login: string;
    avatar_url: string;
  };
}

export async function GET() {
  const token = process.env.GITHUB_TOKEN;
  const username = process.env.GITHUB_USERNAME;

  if (!token) {
    return NextResponse.json(
      { error: "GITHUB_TOKEN no está configurado" },
      { status: 500 }
    );
  }

  try {
    let allRepos: GitHubRepo[] = [];
    let page = 1;
    const perPage = 100;
    let hasMore = true;

    // Obtener información del usuario si no se proporcionó username
    let targetUsername = username;
    if (!targetUsername) {
      const userResponse = await fetch("https://api.github.com/user", {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/vnd.github.v3+json",
        },
      });

      if (!userResponse.ok) {
        throw new Error("Error al obtener información del usuario");
      }

      const userData = await userResponse.json();
      targetUsername = userData.login;
    }

    // Paginación para obtener todos los repos
    while (hasMore) {
      const response = await fetch(
        `https://api.github.com/users/${targetUsername}/repos?per_page=${perPage}&page=${page}&sort=updated&direction=desc`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/vnd.github.v3+json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status}`);
      }

      const repos: GitHubRepo[] = await response.json();
      allRepos = [...allRepos, ...repos];

      if (repos.length < perPage) {
        hasMore = false;
      } else {
        page++;
      }
    }

    return NextResponse.json({ repos: allRepos, username: targetUsername });
  } catch (error) {
    console.error("Error fetching repos:", error);
    return NextResponse.json(
      { error: "Error al obtener repositorios de GitHub" },
      { status: 500 }
    );
  }
}
