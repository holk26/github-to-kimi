"use client";

import { GitHubRepo, getLanguageColor, formatDate } from "@/lib/github";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Star, GitFork, ExternalLink, Terminal, Copy, Check, Loader2 } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";

interface RepoCardProps {
  repo: GitHubRepo;
}

export function RepoCard({ repo }: RepoCardProps) {
  const [copied, setCopied] = useState(false);
  const [opening, setOpening] = useState(false);
  const router = useRouter();

  const kimiCommand = `cd ~/repos 2>/dev/null || mkdir -p ~/repos && cd ~/repos && git clone ${repo.ssh_url} && cd ${repo.name} && kimi`;

  const handleCopyCommand = async () => {
    await navigator.clipboard.writeText(kimiCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenKimi = async () => {
    setOpening(true);
    try {
      // 1. Llamar a la API para clonar el repo en el workspace
      const response = await fetch("/api/kimi/clone", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repoUrl: repo.clone_url,
          repoName: repo.name,
          userId: "default-user",
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || "Error al clonar el repositorio");
      }

      // 2. Redirigir a la terminal con el repo cargado
      router.push(`/terminal?repo=${encodeURIComponent(repo.name)}`);
    } catch (error) {
      console.error("Error opening in Kimi:", error);
      // Fallback: copiar comando al clipboard
      handleCopyCommand();
      alert("No se pudo abrir automáticamente. El comando ha sido copiado al portapapeles.");
    } finally {
      setOpening(false);
    }
  };

  return (
    <Card className="group hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-lg truncate group-hover:text-primary transition-colors">
              {repo.name}
            </h3>
            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
              {repo.description || "Sin descripción"}
            </p>
          </div>
          {repo.private && (
            <Badge variant="secondary" className="shrink-0 text-xs">
              Privado
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex items-center gap-4 text-sm text-muted-foreground mb-4">
          {repo.language && (
            <div className="flex items-center gap-1.5">
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getLanguageColor(repo.language) }}
              />
              <span>{repo.language}</span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4" />
            <span>{repo.stargazers_count.toLocaleString()}</span>
          </div>
          <div className="flex items-center gap-1">
            <GitFork className="w-4 h-4" />
            <span>{repo.forks_count.toLocaleString()}</span>
          </div>
        </div>

        <div className="text-xs text-muted-foreground mb-4">
          Actualizado: {formatDate(repo.updated_at)}
        </div>

        <div className="flex gap-2">
          <Button
            variant="default"
            size="sm"
            className="flex-1 gap-2"
            onClick={handleOpenKimi}
            disabled={opening}
          >
            {opening ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Abriendo...
              </>
            ) : copied ? (
              <>
                <Check className="w-4 h-4" />
                ¡Copiado!
              </>
            ) : (
              <>
                <Terminal className="w-4 h-4" />
                Abrir en Kimi
              </>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() => window.open(repo.html_url, "_blank")}
          >
            <ExternalLink className="w-4 h-4" />
            GitHub
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0"
            onClick={handleCopyCommand}
            title="Copiar comando"
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-500" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </Button>
        </div>

        <div className="mt-3 p-2 bg-muted rounded-md text-xs font-mono text-muted-foreground overflow-x-auto">
          <code className="whitespace-nowrap">{kimiCommand}</code>
        </div>
      </CardContent>
    </Card>
  );
}
