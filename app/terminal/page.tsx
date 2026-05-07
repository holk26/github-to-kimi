"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Trash2 } from "lucide-react";

interface CommandOutput {
  command: string;
  stdout: string;
  stderr: string;
  returncode: number;
}

export default function TerminalPage() {
  const [command, setCommand] = useState("");
  const [history, setHistory] = useState<CommandOutput[]>([]);
  const [loading, setLoading] = useState(false);

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
        body: JSON.stringify({ command: cmd }),
      });

      const data = await res.json();

      setHistory((prev) => [
        ...prev,
        {
          command: cmd,
          stdout: data.stdout || "",
          stderr: data.stderr || "",
          returncode: data.returncode,
        },
      ]);
    } catch (err) {
      setHistory((prev) => [
        ...prev,
        {
          command: cmd,
          stdout: "",
          stderr: "Error de conexión",
          returncode: 1,
        },
      ]);
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-black text-green-400 font-mono text-sm flex flex-col">
      <header className="bg-zinc-900 px-4 py-3 flex items-center justify-between border-b border-zinc-800">
        <span className="text-white font-semibold">Terminal</span>
        <Button variant="ghost" size="sm" onClick={() => setHistory([])} className="text-zinc-400">
          <Trash2 className="w-4 h-4" />
        </Button>
      </header>

      <div className="flex-1 overflow-auto p-4 space-y-2">
        {history.length === 0 && (
          <div className="text-zinc-600 text-center py-12">
            <p>Terminal lista</p>
            <p className="text-xs mt-2">Escribe un comando</p>
          </div>
        )}

        {history.map((item, index) => (
          <div key={index} className="space-y-1">
            <div className="flex items-center gap-2 text-blue-400">
              <span className="text-zinc-600">$</span>
              <span>{item.command}</span>
            </div>
            {item.stdout && (
              <pre className="text-green-400 whitespace-pre-wrap pl-4">{item.stdout}</pre>
            )}
            {item.stderr && (
              <pre className="text-red-400 whitespace-pre-wrap pl-4">{item.stderr}</pre>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={executeCommand} className="flex items-center gap-2 p-3 bg-zinc-900 border-t border-zinc-800">
        <span className="text-blue-400 shrink-0">~ $</span>
        <Input
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder="Comando..."
          className="flex-1 bg-transparent border-0 text-green-400 placeholder:text-zinc-600 focus-visible:ring-0 font-mono"
          disabled={loading}
          autoFocus
        />
        <Button type="submit" size="sm" disabled={loading} variant="ghost" className="text-zinc-400">
          <Send className="w-4 h-4" />
        </Button>
      </form>
    </div>
  );
}
