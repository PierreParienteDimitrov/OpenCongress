"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2, Key, Check, AlertCircle, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  fetchAPIKeys,
  createAPIKey,
  deleteAPIKey,
  type ConfiguredAPIKey,
} from "@/lib/api-client";

const PROVIDERS = [
  {
    value: "anthropic",
    label: "Anthropic (Claude)",
    placeholder: "sk-ant-api03-...",
  },
  { value: "openai", label: "OpenAI (GPT)", placeholder: "sk-..." },
  { value: "google", label: "Google (Gemini)", placeholder: "AIza..." },
] as const;

export function APIKeysManager() {
  const queryClient = useQueryClient();
  const [editingProvider, setEditingProvider] = useState<string | null>(null);
  const [keyInput, setKeyInput] = useState("");
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const { data: keys = [], isLoading } = useQuery<ConfiguredAPIKey[]>({
    queryKey: ["api-keys"],
    queryFn: fetchAPIKeys,
  });

  const saveMutation = useMutation({
    mutationFn: ({
      provider,
      apiKey,
    }: {
      provider: string;
      apiKey: string;
    }) => createAPIKey(provider, apiKey),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      setEditingProvider(null);
      setKeyInput("");
      const label = PROVIDERS.find((p) => p.value === variables.provider)?.label;
      setFeedback({ type: "success", message: `${label} key saved` });
      setTimeout(() => setFeedback(null), 3000);
    },
    onError: (error: Error) => {
      setFeedback({ type: "error", message: error.message });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAPIKey,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      setFeedback({ type: "success", message: "API key deleted" });
      setTimeout(() => setFeedback(null), 3000);
    },
    onError: (error: Error) => {
      setFeedback({ type: "error", message: error.message });
    },
  });

  const isConfigured = (provider: string) =>
    keys.some((k) => k.provider === provider);

  const handleSave = (provider: string) => {
    const trimmed = keyInput.trim();
    if (!trimmed || trimmed.length < 10) {
      setFeedback({ type: "error", message: "API key is too short" });
      return;
    }
    saveMutation.mutate({ provider, apiKey: trimmed });
  };

  return (
    <Card>
      <CardHeader className="py-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Key className="size-5" />
          AI Provider API Keys
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Add your own API key for at least one provider to use the AI chat
          assistant. Keys are encrypted at rest and never sent back to the
          browser.
        </p>

        {feedback && (
          <div
            className={`flex items-center gap-2 rounded-md border px-3 py-2 text-sm ${
              feedback.type === "success"
                ? "border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-200"
                : "border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200"
            }`}
          >
            {feedback.type === "success" ? (
              <Check className="size-4" />
            ) : (
              <AlertCircle className="size-4" />
            )}
            {feedback.message}
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground py-4">
            <Loader2 className="size-4 animate-spin" />
            Loading keys...
          </div>
        ) : (
          <div className="space-y-3">
            {PROVIDERS.map((provider) => {
              const configured = isConfigured(provider.value);
              const existing = keys.find(
                (k) => k.provider === provider.value,
              );
              const isEditing = editingProvider === provider.value;

              return (
                <div
                  key={provider.value}
                  className="rounded-lg border p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">
                        {provider.label}
                      </span>
                      {configured && (
                        <Badge
                          variant="outline"
                          className="text-green-700 border-green-300 dark:text-green-400 dark:border-green-700"
                        >
                          Configured
                        </Badge>
                      )}
                    </div>
                    {configured && !isEditing && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          deleteMutation.mutate(provider.value)
                        }
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="size-4 text-red-500" />
                      </Button>
                    )}
                  </div>

                  {configured && !isEditing && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">
                        Added{" "}
                        {new Date(existing!.created_at).toLocaleDateString()}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setEditingProvider(provider.value);
                          setKeyInput("");
                        }}
                      >
                        Update key
                      </Button>
                    </div>
                  )}

                  {(!configured || isEditing) && (
                    <div className="space-y-2 mt-1">
                      <input
                        type="password"
                        placeholder={provider.placeholder}
                        value={
                          editingProvider === provider.value
                            ? keyInput
                            : ""
                        }
                        onChange={(e) => {
                          if (!isEditing)
                            setEditingProvider(provider.value);
                          setKeyInput(e.target.value);
                        }}
                        onFocus={() => {
                          if (!isEditing) {
                            setEditingProvider(provider.value);
                            setKeyInput("");
                          }
                        }}
                        className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                      />
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={() => handleSave(provider.value)}
                          disabled={saveMutation.isPending}
                        >
                          {saveMutation.isPending && (
                            <Loader2 className="mr-1 size-3 animate-spin" />
                          )}
                          {configured ? "Update" : "Save"}
                        </Button>
                        {isEditing && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setEditingProvider(null);
                              setKeyInput("");
                            }}
                          >
                            Cancel
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
