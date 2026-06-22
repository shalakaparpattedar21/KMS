import { useEffect, useMemo, useState } from "react";
import {
  Bot,
  ExternalLink,
  FileText,
  Inbox,
  Loader2,
  Mail,
  MessageSquare,
  Plus,
  Send,
  Sparkles,
  Trash2,
  User,
} from "lucide-react";
import EmailModal from "../../components/email/EmailModal";

interface Session {
  id: number;
  title: string;
  createdAt?: string;
}

interface Message {
  id: number;
  role: string;
  content: string;
  timestamp?: string;
}

interface Sources {
  documents: { id: number; name: string; web_view_link: string }[];
  emails: {
    id: number;
    subject: string;
    sender: string;
    gmail_message_id: string;
    gmail_url: string;
  }[];
}

interface EmailDetails {
  subject: string;
  sender: string;
  recipient: string;
  received_at: string;
  body: string;
  gmail_message_id: string;
  gmail_thread_id: string;
}

export default function ChatUI() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<Sources>({ documents: [], emails: [] });
  const [selectedEmail, setSelectedEmail] = useState<EmailDetails | null>(null);

  const loadSessions = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/chat/sessions", {
        credentials: "include",
      });
      const data = await response.json();
      setSessions(data);
      if (data.length > 0 && !selectedSession) {
        selectSession(data[0]);
      }
    } catch (error) {
      console.error(error);
    }
  };

  const deleteSession = async (sessionId: number) => {
    const confirmed = window.confirm("Delete this chat?");
    if (!confirmed) return;

    try {
      await fetch(`http://localhost:8000/api/chat/sessions/${sessionId}`, {
        method: "DELETE",
        credentials: "include",
      });

      const updatedSessions = await (
        await fetch("http://localhost:8000/api/chat/sessions", {
          credentials: "include",
        })
      ).json();

      setSessions(updatedSessions);
      setMessages([]);
      setSelectedSession(null);

      if (updatedSessions.length > 0) {
        selectSession(updatedSessions[0]);
      }
    } catch (error) {
      console.error(error);
    }
  };

  const openEmail = async (emailId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/gmail/email/${emailId}`, {
        credentials: "include",
      });

      const data = await response.json();
      setSelectedEmail(data);
    } catch (err) {
      console.error(err);
    }
  };

  const createNewChat = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/chat/sessions", {
        method: "POST",
        credentials: "include",
      });
      const session = await response.json();
      await loadSessions();
      selectSession(session);
    } catch (error) {
      console.error(error);
    }
  };

  const selectSession = async (session: Session) => {
    setSelectedSession(session);
    setSources({ documents: [], emails: [] });
    try {
      const response = await fetch(
        `http://localhost:8000/api/chat/sessions/${session.id}/messages`,
        { credentials: "include" }
      );
      const data = await response.json();
      setMessages(data);
    } catch (error) {
      console.error(error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !selectedSession) return;

    const userMsg = input;
    setInput("");
    setLoading(true);
    setSources({ documents: [], emails: [] });

    setMessages((prev) => [
      ...prev,
      { id: Date.now(), role: "user", content: userMsg },
    ]);

    try {
      const response = await fetch(
        `http://localhost:8000/api/chat/sessions/${selectedSession.id}/messages`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: userMsg }),
        }
      );

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let streamedText = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          streamedText += chunk;

          const sourcesMatch = streamedText.match(/\[SOURCES_START\](.*?)\[SOURCES_END\]/s);

          let displayText = streamedText;
          let extractedSources: Sources = { documents: [], emails: [] };

          if (sourcesMatch) {
            try {
              const sourcesObj = JSON.parse(sourcesMatch[1]);
              extractedSources = sourcesObj.sources ?? { documents: [], emails: [] };
              setSources(extractedSources);
              displayText = streamedText
                .replace(/\[SOURCES_START\].*?\[SOURCES_END\]/s, "")
                .trim();
            } catch (e) {
              console.error("Failed to parse sources:", e);
            }
          }

          setMessages((prev) => {
            const updated = [...prev];
            const lastMsg = updated[updated.length - 1];

            if (lastMsg && lastMsg.role === "assistant") {
              return [...updated.slice(0, -1), { ...lastMsg, content: displayText }];
            } else {
              return [
                ...updated,
                { id: Date.now(), role: "assistant", content: displayText },
              ];
            }
          });
        }
      }

      await loadSessions();
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;

    const loadInitialSessions = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/chat/sessions", {
          credentials: "include",
        });
        const data = await response.json();

        if (!active) return;

        setSessions(data);
        if (data.length > 0) {
          const session = data[0];
          setSelectedSession(session);
          setSources({ documents: [], emails: [] });

          const messagesResponse = await fetch(
            `http://localhost:8000/api/chat/sessions/${session.id}/messages`,
            { credentials: "include" }
          );
          const messagesData = await messagesResponse.json();

          if (active) {
            setMessages(messagesData);
          }
        }
      } catch (error) {
        console.error(error);
      }
    };

    loadInitialSessions();

    return () => {
      active = false;
    };
  }, []);

  const hasSources = sources.documents.length > 0 || sources.emails.length > 0;
  const lastAssistantId = useMemo(
    () => messages.filter((m) => m.role === "assistant").at(-1)?.id,
    [messages]
  );

  const suggestions = [
    "Summarize recent institutional updates",
    "Find emails about admissions",
    "Search Drive documents for policy references",
    "Compare related documents",
  ];

  return (
    <div className="flex h-full min-h-[calc(100vh-120px)] overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-xl shadow-zinc-950/5">
      <aside className="hidden w-80 shrink-0 flex-col border-r border-zinc-800 bg-[#121214] text-white md:flex">
        <div className="border-b border-white/10 p-4">
          <div className="mb-4 flex items-center gap-3 px-1">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#A61E22] text-sm font-black shadow-lg shadow-[#A61E22]/20">
              R
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-red-200">RIIDL</p>
              <h2 className="text-sm font-semibold">Knowledge AI</h2>
            </div>
          </div>

          <button
            onClick={createNewChat}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-white px-4 py-3 text-sm font-semibold text-zinc-950 transition hover:bg-zinc-100"
          >
            <Plus size={17} />
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 kms-scrollbar">
          <p className="mb-2 px-2 text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
            Sessions
          </p>

          {sessions.length === 0 ? (
            <div className="mt-8 flex flex-col items-center justify-center rounded-lg border border-white/10 bg-white/[0.03] p-6 text-center text-sm text-zinc-400">
              <Inbox size={30} className="mb-3 text-zinc-500" />
              No conversations yet
            </div>
          ) : (
            <div className="space-y-1">
              {sessions.map((session) => {
                const active = selectedSession?.id === session.id;
                return (
                  <div
                    key={session.id}
                    onClick={() => selectSession(session)}
                    className={`group flex cursor-pointer items-start gap-3 rounded-lg px-3 py-3 transition ${
                      active
                        ? "bg-[#A61E22] text-white shadow-lg shadow-[#A61E22]/20"
                        : "text-zinc-300 hover:bg-white/8 hover:text-white"
                    }`}
                  >
                    <MessageSquare size={16} className="mt-0.5 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{session.title}</p>
                      <p className={`mt-1 text-xs ${active ? "text-red-100" : "text-zinc-500"}`}>
                        {session.createdAt || "Recent"}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteSession(session.id);
                      }}
                      className={`rounded-md p-1 opacity-0 transition group-hover:opacity-100 ${
                        active ? "hover:bg-white/15" : "hover:bg-white/10 hover:text-red-200"
                      }`}
                      title="Delete chat"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col bg-[#fbfaf9]">
        <header className="border-b border-zinc-200 bg-white px-5 py-4 md:px-8">
          <div className="flex items-center justify-between gap-4">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#A61E22]">
                AI Search
              </p>
              <h1 className="truncate text-lg font-semibold text-zinc-950">
                {selectedSession?.title || "Enterprise Knowledge Assistant"}
              </h1>
            </div>
            <div className="hidden items-center gap-2 rounded-full border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs font-medium text-zinc-600 sm:flex">
              <Sparkles size={14} className="text-[#A61E22]" />
              RAG-enabled responses
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-6 kms-scrollbar md:px-8">
          <div className="mx-auto flex max-w-4xl flex-col gap-6">
            {messages.length === 0 ? (
              <div className="flex min-h-[52vh] flex-col items-center justify-center text-center">
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-lg bg-[#A61E22] text-white shadow-lg shadow-[#A61E22]/20">
                  <Bot size={28} />
                </div>
                <h2 className="text-2xl font-semibold text-zinc-950">Ask across RIIDL knowledge</h2>
                <p className="mt-3 max-w-xl text-sm leading-6 text-zinc-600">
                  Search Gmail, Drive documents, and institutional context in one conversation with source-backed answers.
                </p>
                <div className="mt-8 grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => setInput(suggestion)}
                      className="rounded-lg border border-zinc-200 bg-white px-4 py-3 text-left text-sm font-medium text-zinc-700 shadow-sm transition hover:border-[#A61E22]/30 hover:text-[#A61E22] hover:shadow-md"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => {
                const isUser = msg.role === "user";
                return (
                  <div key={msg.id} className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
                    {!isUser && (
                      <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-zinc-950 text-white">
                        <Bot size={18} />
                      </div>
                    )}

                    <div className={`max-w-[min(720px,92%)] ${isUser ? "order-first" : ""}`}>
                      <div
                        className={`rounded-2xl px-5 py-4 text-sm leading-7 shadow-sm ${
                          isUser
                            ? "rounded-tr-md bg-[#A61E22] text-white shadow-[#A61E22]/15"
                            : "rounded-tl-md border border-zinc-200 bg-white text-zinc-800"
                        }`}
                      >
                        <div className="whitespace-pre-wrap">{msg.content}</div>

                        {!isUser && hasSources && msg.id === lastAssistantId && (
                          <div className="mt-5 border-t border-zinc-200 pt-4">
                            <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
                              <Sparkles size={14} className="text-[#A61E22]" />
                              Sources
                            </div>

                            {sources.documents.length > 0 && (
                              <div className="mb-4 space-y-2">
                                <p className="text-xs font-semibold text-zinc-500">Documents</p>
                                {sources.documents.map((doc) => (
                                  <a
                                    key={doc.id}
                                    href={doc.web_view_link}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="flex items-center justify-between gap-3 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs font-medium text-zinc-700 transition hover:border-[#A61E22]/25 hover:bg-white hover:text-[#A61E22]"
                                  >
                                    <span className="flex min-w-0 items-center gap-2">
                                      <FileText size={15} className="shrink-0" />
                                      <span className="truncate">{doc.name}</span>
                                    </span>
                                    <ExternalLink size={14} className="shrink-0" />
                                  </a>
                                ))}
                              </div>
                            )}

                            {sources.emails.length > 0 && (
                              <div className="space-y-2">
                                <p className="text-xs font-semibold text-zinc-500">Emails</p>
                                {sources.emails.map((email) => (
                                  <button
                                    key={email.id}
                                    onClick={() => openEmail(email.id)}
                                    className="flex w-full items-start gap-3 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-3 text-left text-xs transition hover:border-[#A61E22]/25 hover:bg-white"
                                  >
                                    <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[#A61E22]/10 text-[#A61E22]">
                                      <Mail size={15} />
                                    </span>
                                    <span className="min-w-0">
                                      <span className="block truncate font-semibold text-zinc-800">
                                        {email.subject}
                                      </span>
                                      <span className="mt-1 block truncate text-zinc-500">{email.sender}</span>
                                    </span>
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    {isUser && (
                      <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-zinc-200 text-zinc-700">
                        <User size={18} />
                      </div>
                    )}
                  </div>
                );
              })
            )}

            {loading && (
              <div className="flex justify-start gap-3">
                <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-zinc-950 text-white">
                  <Bot size={18} />
                </div>
                <div className="rounded-2xl rounded-tl-md border border-zinc-200 bg-white px-5 py-4 shadow-sm">
                  <div className="flex items-center gap-2 text-sm font-medium text-zinc-500">
                    <Loader2 size={16} className="animate-spin text-[#A61E22]" />
                    Searching enterprise knowledge
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-zinc-200 bg-white px-4 py-4 md:px-8">
          <div className="mx-auto max-w-4xl">
            <div className="flex items-end gap-3 rounded-lg border border-zinc-200 bg-zinc-50 p-2 shadow-sm focus-within:border-[#A61E22]/60 focus-within:bg-white focus-within:shadow-[0_0_0_4px_rgba(166,30,34,0.08)]">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="Ask about Gmail, Drive, documents, or institutional knowledge..."
                rows={1}
                className="max-h-36 min-h-11 flex-1 resize-none bg-transparent px-3 py-3 text-sm text-zinc-900 outline-none placeholder:text-zinc-400"
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-[#A61E22] text-white shadow-md shadow-[#A61E22]/20 transition hover:bg-[#8f181c] disabled:opacity-45"
                title="Send message"
              >
                {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
              </button>
            </div>
          </div>
        </div>
      </section>

      {selectedEmail && <EmailModal email={selectedEmail} onClose={() => setSelectedEmail(null)} />}
    </div>
  );
}



