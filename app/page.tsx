"use client";

import { useEffect, useState } from "react";
import { fetchRepos, ReposResponse } from "@/lib/github";
import { RepoList } from "@/components/RepoList";
import { Button } from "@/components/ui/button";
import { Terminal, RefreshCw, AlertCircle } from "lucide-react";

export default function Home() {
  const [data, setData] = useState<ReposResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRepos = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchRepos();
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRepos();
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center">
              <Terminal className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight">Kimi Workspace</h1>
              <p className="text-xs text-muted-foreground leading-tight">
                Repositorios → Terminal
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadRepos}
              disabled={loading}
              className="gap-2"
            >
              <RefreshCw
                className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
              />
              <span className="hidden sm:inline">
                {loading ? "Cargando..." : "Actualizar"}
              </span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && !data ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
            <p className="mt-4 text-muted-foreground animate-pulse">
              Cargando repositorios...
            </p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mb-4">
              <AlertCircle className="w-8 h-8 text-destructive" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Error al cargar</h2>
            <p className="text-muted-foreground text-center max-w-md mb-6">
              {error}
            </p>
            <Button onClick={loadRepos} variant="outline" className="gap-2">
              <RefreshCw className="w-4 h-4" />
              Reintentar
            </Button>
          </div>
        ) : data ? (
          <RepoList repos={data.repos} username={data.username} />
        ) : null}
      </main>

      {/* Footer */}
      <footer className="border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between text-sm text-muted-foreground">
          <p>GitHub → Kimi CLI</p>
          <p>
            Configura{" "}
            <code className="bg-muted px-1.5 py-0.5 rounded text-xs">
              GITHUB_TOKEN
            </code>{" "}
            en tu servidor
          </p>
        </div>
      </footer>
    </div>
  );
}
