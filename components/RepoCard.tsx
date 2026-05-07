"use client";

import { GitHubRepo, getLanguageColor, formatDate } from "@/lib/github";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Star, GitFork, ExternalLink, Terminal, Loader2 } from "lucide-react";
import { useState } from "react";

interface RepoCardProps {
  repo: GitHubRepo;
  onOpenTerminal?: (repo: { clone_url: string; name: string }) => void;
}

export function RepoCard({ repo, onOpenTerminal }: RepoCardProps) {
  const [loading, setLoading] = useState(false);

  const handleOpenTerminal = async () => {
    if (!onOpenTerminal) return;
    setLoading(true);
    await onOpenTerminal({ clone_url: repo.clone_url, name: repo.name });
    setLoading(false);
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
            onClick={handleOpenTerminal}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Terminal className="w-4 h-4" />
            )}
            {loading ? "Abriendo..." : "Abrir en Kimi"}
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
        </div>
      </CardContent>
    </Card>
  );
}
