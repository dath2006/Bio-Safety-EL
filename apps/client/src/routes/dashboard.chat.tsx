import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Bot, Loader2, Send, User, Brain, ChevronDown, ChevronUp, CheckCircle2, Trash2, Plus } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api } from "@/lib/haccp/api";
import type { ChatResponse } from "@/lib/haccp/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/dashboard/chat")({
  component: ChatPage,
});

import { FOOD_CATEGORIES } from "@/lib/haccp/categories";

const CATEGORIES = FOOD_CATEGORIES.map((c) => c.label);
const SUGGESTIONS = [
  "FSSAI critical limits for pasteurization",
  "Biological hazards in RTE meals",
  "Cold chain temperature requirements",
  "Allergen labelling under FSSAI",
];

type Msg = { role: "user" | "assistant"; text: string; meta?: ChatResponse };

interface ChatSession {
  id: string;
  title: string;
  category: string;
  messages: Msg[];
  createdAt: string;
}

interface ParsedMessage {
  thinking?: string;
  response: string;
  isThinkingComplete: boolean;
}

function parseThinkingAndResponse(text: string): ParsedMessage {
  const thinkingStart = text.indexOf("<thinking>");
  const thinkingEnd = text.indexOf("</thinking>");

  if (thinkingStart !== -1) {
    if (thinkingEnd !== -1) {
      return {
        thinking: text.slice(thinkingStart + 10, thinkingEnd).trim(),
        response: text.slice(thinkingEnd + 11).trim(),
        isThinkingComplete: true,
      };
    } else {
      return {
        thinking: text.slice(thinkingStart + 10).trim(),
        response: "",
        isThinkingComplete: false,
      };
    }
  }

  return {
    thinking: undefined,
    response: text,
    isThinkingComplete: true,
  };
}

function AssistantMessageContent({ text }: { text: string }) {
  const [collapsed, setCollapsed] = useState(false);
  const { thinking, response, isThinkingComplete } = parseThinkingAndResponse(text);

  return (
    <div className="space-y-3">
      {thinking !== undefined && (
        <div className="rounded-lg border border-border bg-muted/40 overflow-hidden transition-all duration-300">
          <button
            type="button"
            onClick={() => setCollapsed(!collapsed)}
            className="flex items-center justify-between w-full px-3 py-2 text-[11px] font-semibold text-muted-foreground hover:bg-accent/40 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <Brain className={cn("h-3.5 w-3.5 text-primary", !isThinkingComplete && "animate-pulse")} />
              <span>
                {isThinkingComplete ? "Reasoning & Context Search Complete" : "Reasoning & Retrieval Audit..."}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {!isThinkingComplete ? (
                <span className="flex h-1.5 w-1.5 rounded-full bg-primary animate-ping" />
              ) : (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              )}
              {collapsed ? <ChevronDown className="h-3 w-3" /> : <ChevronUp className="h-3 w-3" />}
            </div>
          </button>
          {!collapsed && (
            <div className="px-3 pb-3 pt-1 border-t border-border/40 text-xs font-mono text-muted-foreground/90 whitespace-pre-wrap leading-relaxed max-h-[180px] overflow-y-auto bg-muted/10">
              {thinking || "Analyzing food safety guidelines..."}
            </div>
          )}
        </div>
      )}
      
      {response && (
        <div className="prose prose-sm max-w-none text-sm leading-relaxed
          [&_h1]:text-base [&_h1]:font-bold [&_h1]:mb-2 [&_h1]:mt-3
          [&_h2]:text-sm [&_h2]:font-semibold [&_h2]:mb-1.5 [&_h2]:mt-3
          [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:mb-1 [&_h3]:mt-2
          [&_p]:mb-2 [&_p:last-child]:mb-0
          [&_ul]:list-disc [&_ul]:pl-4 [&_ul]:mb-2 [&_ul]:space-y-0.5
          [&_ol]:list-decimal [&_ol]:pl-4 [&_ol]:mb-2 [&_ol]:space-y-0.5
          [&_li]:text-sm
          [&_strong]:font-semibold
          [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-xs [&_code]:font-mono
          [&_pre]:bg-muted [&_pre]:p-3 [&_pre]:rounded-md [&_pre]:overflow-x-auto [&_pre]:mb-2
          [&_blockquote]:border-l-2 [&_blockquote]:border-primary/40 [&_blockquote]:pl-3 [&_blockquote]:italic [&_blockquote]:text-muted-foreground
          [&_table]:w-full [&_table]:text-xs [&_table]:border-collapse [&_table]:mb-2
          [&_th]:border [&_th]:border-border [&_th]:px-2 [&_th]:py-1 [&_th]:bg-muted [&_th]:font-medium [&_th]:text-left
          [&_td]:border [&_td]:border-border [&_td]:px-2 [&_td]:py-1
          [&_hr]:my-2 [&_hr]:border-border
        ">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {response}
          </ReactMarkdown>
        </div>
      )}
      {!response && thinking !== undefined && !isThinkingComplete && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground italic pl-1">
          <Loader2 className="h-3 w-3 animate-spin text-primary" />
          <span>Generating FSSAI compliance details...</span>
        </div>
      )}
    </div>
  );
}

function ChatPage() {
  const [category, setCategory] = useState<string>(CATEGORIES[0]);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [loading, setLoading] = useState(false);
  
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  // Load sessions from LocalStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("haccp_chat_sessions");
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as ChatSession[];
        setSessions(parsed);
        if (parsed.length > 0) {
          setActiveSessionId(parsed[0].id);
          setCategory(parsed[0].category);
          setMessages(parsed[0].messages);
        } else {
          initDefaultSession();
        }
      } catch (e) {
        initDefaultSession();
      }
    } else {
      initDefaultSession();
    }
  }, []);

  function initDefaultSession() {
    const newId = "chat_" + Date.now().toString(36);
    const defaultS: ChatSession = {
      id: newId,
      title: "New Q&A Session",
      category: CATEGORIES[0],
      messages: [],
      createdAt: new Date().toISOString(),
    };
    setSessions([defaultS]);
    setActiveSessionId(newId);
    setCategory(CATEGORIES[0]);
    setMessages([]);
    localStorage.setItem("haccp_chat_sessions", JSON.stringify([defaultS]));
  }

  function createNewSession() {
    const newId = "chat_" + Date.now().toString(36);
    const newS: ChatSession = {
      id: newId,
      title: "New Q&A Session",
      category: category,
      messages: [],
      createdAt: new Date().toISOString(),
    };
    const updated = [newS, ...sessions];
    setSessions(updated);
    setActiveSessionId(newId);
    setMessages([]);
    localStorage.setItem("haccp_chat_sessions", JSON.stringify(updated));
  }

  function selectSession(id: string) {
    const sess = sessions.find((s) => s.id === id);
    if (!sess) return;
    setActiveSessionId(id);
    setCategory(sess.category);
    setMessages(sess.messages);
  }

  function deleteSession(id: string) {
    const updated = sessions.filter((s) => s.id !== id);
    setSessions(updated);
    localStorage.setItem("haccp_chat_sessions", JSON.stringify(updated));
    
    if (activeSessionId === id) {
      if (updated.length > 0) {
        setActiveSessionId(updated[0].id);
        setCategory(updated[0].category);
        setMessages(updated[0].messages);
      } else {
        initDefaultSession();
      }
    }
  }

  function handleCategoryChange(newCat: string) {
    setCategory(newCat);
    setSessions((prev) => {
      const updated = prev.map((s) =>
        s.id === activeSessionId ? { ...s, category: newCat } : s
      );
      localStorage.setItem("haccp_chat_sessions", JSON.stringify(updated));
      return updated;
    });
  }

  async function send(text: string) {
    if (!text.trim() || loading || !activeSessionId) return;
    
    const userMsg: Msg = { role: "user", text };
    const initialAssistantMsg: Msg = { role: "assistant", text: "" };
    
    const currentMessages = [...messages, userMsg];
    setMessages([...currentMessages, initialAssistantMsg]);
    setInput("");
    setLoading(true);

    let sessionTitle = sessions.find((s) => s.id === activeSessionId)?.title;
    const isFirstMsg = currentMessages.length === 1;
    if (isFirstMsg && (!sessionTitle || sessionTitle === "New Q&A Session")) {
      sessionTitle = text.length > 25 ? text.slice(0, 25).trim() + "..." : text;
    }

    setSessions((prev) => {
      const updated = prev.map((s) =>
        s.id === activeSessionId
          ? {
              ...s,
              title: sessionTitle || s.title,
              messages: [...s.messages, userMsg],
            }
          : s
      );
      localStorage.setItem("haccp_chat_sessions", JSON.stringify(updated));
      return updated;
    });
    
    let streamMeta: ChatResponse | undefined = undefined;
    
    try {
      let accumulatedText = "";
      await api.chatStream(
        text,
        category,
        (chunk) => {
          accumulatedText += chunk;
          setMessages((m) => {
            const next = [...m];
            if (next.length > 0) {
              next[next.length - 1] = {
                ...next[next.length - 1],
                text: accumulatedText,
              };
            }
            return next;
          });
        },
        (meta) => {
          streamMeta = meta;
          setMessages((m) => {
            const next = [...m];
            if (next.length > 0) {
              next[next.length - 1] = {
                ...next[next.length - 1],
                meta,
              };
            }
            return next;
          });
        }
      );

      setSessions((prev) => {
        const updated = prev.map((s) => {
          if (s.id === activeSessionId) {
            return {
              ...s,
              title: sessionTitle || s.title,
              messages: [
                ...s.messages,
                { role: "assistant" as const, text: accumulatedText, meta: streamMeta },
              ],
            };
          }
          return s;
        });
        localStorage.setItem("haccp_chat_sessions", JSON.stringify(updated));
        return updated;
      });
    } catch (e) {
      setMessages((m) => {
        const next = [...m];
        if (next.length > 0) {
          next[next.length - 1] = {
            ...next[next.length - 1],
            text: `Error during streaming: ${(e as Error).message}`,
          };
        }
        return next;
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-6 h-full">
      <aside className="rounded-xl border border-border bg-card p-4 space-y-6 h-fit max-h-[85vh] overflow-y-auto">
        <div>
          <Button
            onClick={createNewSession}
            className="w-full text-xs gap-2 cursor-pointer"
            variant="outline"
          >
            <Plus className="h-3.5 w-3.5" /> New Chat
          </Button>
        </div>

        {sessions.length > 0 && (
          <div>
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Recent Chats
            </div>
            <div className="mt-2 space-y-1">
              {sessions.map((s) => (
                <div
                  key={s.id}
                  className={cn(
                    "group flex items-center justify-between rounded-md px-2.5 py-1.5 text-xs transition text-left cursor-pointer",
                    activeSessionId === s.id
                      ? "bg-accent text-accent-foreground font-semibold"
                      : "hover:bg-accent/40 text-muted-foreground"
                  )}
                  onClick={() => selectSession(s.id)}
                >
                  <span className="truncate flex-1 pr-2">
                    {s.title}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(s.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 hover:text-destructive transition-opacity cursor-pointer p-0.5"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Food category
          </div>
          <div className="mt-2 space-y-1">
            {CATEGORIES.map((c) => (
              <button
                key={c}
                onClick={() => handleCategoryChange(c)}
                className={cn(
                  "w-full text-left text-xs rounded-md px-3 py-1.5 transition cursor-pointer",
                  category === c
                    ? "bg-primary text-primary-foreground font-semibold"
                    : "hover:bg-accent",
                )}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Suggestions
          </div>
          <div className="mt-2 space-y-1.5">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="w-full text-left text-[11px] rounded-md border border-border bg-background px-3 py-2 hover:bg-accent transition cursor-pointer"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </aside>

      <section className="flex flex-col rounded-xl border border-border bg-card min-h-[60vh] h-[80vh]">
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {messages.length === 0 && (
            <div className="text-center text-sm text-muted-foreground mt-16">
              Ask anything about FSSAI Schedule 4, Codex CAC/RCP, or your
              process. Answers are grounded in cited regulatory sources.
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className="flex gap-3">
              <div
                className={cn(
                  "h-8 w-8 rounded-md flex items-center justify-center shrink-0",
                  m.role === "user"
                    ? "bg-secondary text-secondary-foreground"
                    : "bg-primary text-primary-foreground",
                )}
              >
                {m.role === "user" ? (
                  <User className="h-4 w-4" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                {m.role === "user" ? (
                  <div className="text-sm text-foreground whitespace-pre-wrap">{m.text}</div>
                ) : (
                  <AssistantMessageContent text={m.text} />
                )}
                
                {m.meta && m.meta.sources && m.meta.sources.length > 0 && (
                  <div className="mt-3 space-y-2">
                    <span
                      className={cn(
                        "inline-block text-[11px] px-2 py-0.5 rounded-full border",
                        m.meta.confidence === "high" &&
                          "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
                        m.meta.confidence === "medium" &&
                          "bg-amber-500/10 text-amber-500 border-amber-500/20",
                        m.meta.confidence === "low" &&
                          "bg-rose-500/10 text-rose-500 border-rose-500/20",
                      )}
                    >
                      Confidence: {m.meta.confidence}
                    </span>
                    <Accordion type="single" collapsible>
                      <AccordionItem value="src" className="border-none">
                        <AccordionTrigger className="text-xs py-2 cursor-pointer">
                          {m.meta.sources.length} citation
                          {m.meta.sources.length === 1 ? "" : "s"}
                        </AccordionTrigger>
                        <AccordionContent>
                          <ul className="text-xs text-muted-foreground space-y-1">
                            {m.meta.sources.map((s) => (
                              <li key={s}>• {s}</li>
                            ))}
                          </ul>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && messages[messages.length - 1]?.text === "" && (
            <div className="flex gap-3 items-center text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin text-primary" /> Searching regulations…
            </div>
          )}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="border-t border-border p-3 flex gap-2"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask about ${category}…`}
          />
          <Button type="submit" disabled={loading} className="cursor-pointer">
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </section>
    </div>
  );
}