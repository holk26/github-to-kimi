"use client";

import { useState, useMemo } from "react";
import { GitHubRepo } from "@/lib/github";
import { RepoCard } from "./RepoCard";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, X } from "lucide-react";

interface RepoListProps {
  repos: GitHubRepo[];
  username: string;
  onOpenTerminal?: (repo: { clone_url: string; name: string }) => void;
}

export function RepoList({ repos, username, onOpenTerminal }: RepoListProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);

  const languages = useMemo(() => {
    const langSet = new Set<string>();
    repos.forEach((repo) => {
      if (repo.language) langSet.add(repo.language);
    });
    return Array.from(langSet).sort();
  }, [repos]);

  const filteredRepos = useMemo(() => {
    return repos.filter((repo) => {
      const matchesSearch =
        !searchQuery ||
        repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (repo.description?.toLowerCase().includes(searchQuery.toLowerCase()) ??
          false);

      const matchesLanguage =
        !selectedLanguage || repo.language === selectedLanguage;

      return matchesSearch && matchesLanguage;
    });
  }, [repos, searchQuery, selectedLanguage]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">
            Repositorios de{" "}
            <span className="text-primary">{username}</span>
          </h2>
          <p className="text-muted-foreground mt-1">
            {repos.length} repositorios en total
          </p>
        </div>
      </div>

      <div className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Buscar repositorios..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2"
            >
              <X className="w-4 h-4 text-muted-foreground hover:text-foreground" />
            </button>
          )}
        </div>

        {languages.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <span className="text-sm text-muted-foreground py-1">
              Filtrar por:
            </span>
            <Badge
              variant={selectedLanguage === null ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setSelectedLanguage(null)}
            >
              Todos
            </Badge>
            {languages.map((lang) => (
              <Badge
                key={lang}
                variant={selectedLanguage === lang ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() =>
                  setSelectedLanguage(
                    selectedLanguage === lang ? null : lang
                  )
                }
              >
                {lang}
              </Badge>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          Mostrando {filteredRepos.length} de {repos.length} repositorios
        </span>
        {(searchQuery || selectedLanguage) && (
          <button
            onClick={() => {
              setSearchQuery("");
              setSelectedLanguage(null);
            }}
            className="text-primary hover:underline"
          >
            Limpiar filtros
          </button>
        )}
      </div>

      {filteredRepos.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredRepos.map((repo) => (
            <RepoCard 
              key={repo.id} 
              repo={repo} 
              onOpenTerminal={onOpenTerminal}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-muted-foreground text-lg">
            No se encontraron repositorios
          </p>
          <p className="text-muted-foreground text-sm mt-1">
            Intenta con otros términos de búsqueda
          </p>
        </div>
      )}
    </div>
  );
}
