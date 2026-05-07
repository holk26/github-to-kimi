"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Send, Trash2, FolderGit } from "lucide-react";

interface CommandOutput {
  command: string;
  stdout: string;
  stderr: string;
  returncode: number;
  timestamp: Date;
}

export default function TerminalPage() {
  const searchParams = useSearchParams();
  const repoName = searchParams.get("repo");
  const repoPath = searchParams.get("path");

  const [command, setCommand] = useState("");
  const [history, setHistory] = useState<CommandOutput[]>([]);
  const [loading, setLoading] = useState(false);
  const [cwd, setCwd] = useState(repoPath || "/workspace");
  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const executeCommand = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!command.trim() || loading) return;

    setLoading(true);
    const cmd = command.trim();
    setCommand("");

    try {
      const res = await fetch("/api/kimi/exec", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd, cwd }),
      });

      const data = await res.json();

      setHistory((prev) => [
        ...prev,
        {
          command: cmd,
          stdout: data.stdout || "",
          stderr: data.stderr || "",
          returncode: data.returncode,
          timestamp: new Date(),
        },
      ]);

      if (data.cwd) {
        setCwd(data.cwd);
      }
    } catch (error) {
      setHistory((prev) => [
        ...prev,
        {
          command: cmd,
          stdout: "",
          stderr: "Error de conexión con el servidor",
          returncode: 1,
          timestamp: new Date(),
        },
      ]);
    }

    setLoading(false);
  };

  const clearHistory = () => setHistory([]);

  const runKimi = () => {
    setCommand("kimi");
    executeCommand();
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b bg-card/50 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FolderGit className="w-5 h-5 text-primary" />
          <div>
            <h1 className="font-semibold">Terminal</h1>
            {repoName && (
              <p className="text-xs text-muted-foreground">{repoName}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={runKimi}>
            Ejecutar Kimi
          </Button>
          <Button variant="ghost" size="sm" onClick={clearHistory}>
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </header>

      {/* Terminal Output */}
      <div className="flex-1 overflow-auto p-4 font-mono text-sm">
        <div className="space-y-4">
          {history.length === 0 && (
            <div className="text-muted-foreground text-center py-12">
              <p>Terminal lista. Escribe un comando para empezar.</p>
              <p className="text-xs mt-2">Prueba: git status, ls, kimi</p>
            </div>
          )}

          {history.map((item, index) => (
            <div key={index} className="space-y-1">
              <div className="flex items-center gap-2 text-primary">
                <span className="text-muted-foreground">$</span>
                <span>{item.command}</span>
              </div>
              {item.stdout && (
                <pre className="text-foreground whitespace-pre-wrap pl-4">
                  {item.stdout}
                </pre>
              )}
              {item.stderr && (
                <pre className="text-destructive whitespace-pre-wrap pl-4">
                  {item.stderr}
                </pre>
              )}
              {item.returncode !== 0 && (
                <p className="text-destructive text-xs pl-4">
                  Exit code: {item.returncode}
                </p>
              )}
            </div>
          ))}
          <div ref={terminalEndRef} />
        </div>
      </div>

      {/* Input */}
      <Card className="m-4 p-3">
        <form onSubmit={executeCommand} className="flex items-center gap-2">
          <span className="text-primary font-mono text-sm shrink-0">
            {cwd.replace("/workspace", "~")} $
          </span>
          <Input
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="Escribe un comando..."
            className="flex-1 font-mono"
            disabled={loading}
            autoFocus
          />
          <Button type="submit" size="sm" disabled={loading}>
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </Card>
    </div>
  );
}
