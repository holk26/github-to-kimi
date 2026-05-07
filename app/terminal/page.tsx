"use client";

import { useState, useEffect, Suspense } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Trash2, FolderGit, Home } from "lucide-react";
import { useSearchParams, useRouter } from "next/navigation";

interface CommandOutput {
  command: string;
  stdout: string;
  stderr: string;
  returncode: number;
}

function TerminalContent() {
  const [command, setCommand] = useState("");
  const [history, setHistory] = useState<CommandOutput[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentRepo, setCurrentRepo] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const repo = searchParams.get("repo");
    if (repo) {
      setCurrentRepo(repo);
      // Ejecutar ls automáticamente al cargar con un repo
      executeCommandInternal("ls -la");
    }
  }, [searchParams]);

  const executeCommandInternal = async (cmd: string) => {
    setLoading(true);

    try {
      const res = await fetch("/api/kimi/exec", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd }),
      });

      const data = await res.json();

      setHistory((prev) => [
        ...prev,
        {
          command: cmd,
          stdout: data.output || data.stdout || "",
          stderr: data.error || data.stderr || "",
          returncode: data.returncode ?? 0,
        },
      ]);
    } catch (err) {
      setHistory((prev) => [
        ...prev,
        {
          command: cmd,
          stdout: "",
          stderr: "Error de conexión: " + String(err),
          returncode: 1,
        },
      ]);
    }

    setLoading(false);
  };

  const executeCommand = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!command.trim() || loading) return;

    const cmd = command.trim();
    setCommand("");
    await executeCommandInternal(cmd);
  };

  return (
    <div className="min-h-screen bg-black text-green-400 font-mono text-sm flex flex-col">
      {/* Header */}
      <header className="bg-zinc-900 px-4 py-3 flex items-center justify-between border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <span className="text-white font-semibold">Terminal</span>
          {currentRepo && (
            <div className="flex items-center gap-1.5 px-2 py-1 bg-zinc-800 rounded-md">
              <FolderGit className="w-3.5 h-3.5 text-blue-400" />
              <span className="text-xs text-zinc-300">{currentRepo}</span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/")}
            className="text-zinc-400 hover:text-white"
            title="Volver al inicio"
          >
            <Home className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setHistory([])}
            className="text-zinc-400 hover:text-white"
            title="Limpiar terminal"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </header>

      {/* Output area */}
      <div className="flex-1 overflow-auto p-4 space-y-2">
        {history.length === 0 && (
          <div className="text-zinc-600 text-center py-12">
            <p>Terminal lista</p>
            <p className="text-xs mt-2">
              {currentRepo
                ? `Repositorio cargado: ${currentRepo}`
                : "Escribe un comando o selecciona un repositorio"}
            </p>
          </div>
        )}

        {history.map((item, index) => (
          <div key={index} className="space-y-1">
            <div className="flex items-center gap-2 text-blue-400">
              <span className="text-zinc-600">$</span>
              <span>{item.command}</span>
            </div>
            {item.stdout && (
              <pre className="text-green-400 whitespace-pre-wrap pl-4">
                {item.stdout}
              </pre>
            )}
            {item.stderr && (
              <pre className="text-red-400 whitespace-pre-wrap pl-4">
                {item.stderr}
              </pre>
            )}
            {item.returncode !== 0 && !item.stderr && (
              <pre className="text-red-400 whitespace-pre-wrap pl-4">
                Error (código: {item.returncode})
              </pre>
            )}
          </div>
        ))}
      </div>

      {/* Input */}
      <form
        onSubmit={executeCommand}
        className="flex items-center gap-2 p-3 bg-zinc-900 border-t border-zinc-800"
      >
        <span className="text-blue-400 shrink-0">
          {currentRepo ? `~/${currentRepo} $` : "~ $"}
        </span>
        <Input
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder="Comando..."
          className="flex-1 bg-transparent border-0 text-green-400 placeholder:text-zinc-600 focus-visible:ring-0 font-mono"
          disabled={loading}
          autoFocus
        />
        <Button
          type="submit"
          size="sm"
          disabled={loading}
          variant="ghost"
          className="text-zinc-400"
        >
          <Send className="w-4 h-4" />
        </Button>
      </form>
    </div>
  );
}

export default function TerminalPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black text-green-400 font-mono flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-green-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p>Cargando terminal...</p>
          </div>
        </div>
      }
    >
      <TerminalContent />
    </Suspense>
  );
}
