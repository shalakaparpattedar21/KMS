import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
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

export default function ChatUI() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<Sources>({ documents: [], emails: [] });
  const [selectedEmail, setSelectedEmail] =
  useState<any>(null);

  useEffect(() => {
    loadSessions();
  }, []);

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
  const openEmail = async (
      emailId: number
    ) => {

      try {

        const response = await fetch(
          `http://localhost:8000/api/gmail/email/${emailId}`,
          {
            credentials: "include"
          }
        );

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

          const sourcesMatch = streamedText.match(
            /\[SOURCES_START\](.*?)\[SOURCES_END\]/s
          );

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
              return [
                ...updated.slice(0, -1),
                { ...lastMsg, content: displayText },
              ];
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

  const hasSources =
    sources.documents.length > 0 || sources.emails.length > 0;

  return (
    <div className="flex h-[calc(100vh-100px)] bg-white text-gray-900 rounded-xl shadow-lg overflow-hidden">
      <style>{`
        .sidebar-gradient {
          background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        }
        .message-user { animation: slideInRight 0.3s ease-out; }
        .message-assistant { animation: slideInLeft 0.3s ease-out; }
        @keyframes slideInRight {
          from { opacity: 0; transform: translateX(20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes slideInLeft {
          from { opacity: 0; transform: translateX(-20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .session-item { transition: all 0.2s ease; }
        .session-item:hover {
          background-color: rgba(59, 130, 246, 0.05);
          transform: translateX(4px);
        }
        .input-focus { transition: all 0.2s ease; }
        .input-focus:focus { box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
      `}</style>

      {/* Sidebar */}
      <div className="w-72 sidebar-gradient border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={createNewChat}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg py-2.5 hover:from-blue-700 hover:to-blue-800 transition-all font-medium text-sm"
          >
            <i className="ti ti-plus" style={{ fontSize: "18px" }}></i>
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {sessions.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              <i
                className="ti ti-inbox"
                style={{ fontSize: "32px", opacity: 0.4, display: "block", marginBottom: "8px" }}
              ></i>
              No conversations yet
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => selectSession(session)}
                className={`session-item p-4 cursor-pointer border-b border-gray-100 group flex items-center justify-between ${
                  selectedSession?.id === session.id
                    ? "bg-blue-50 border-l-4 border-l-blue-600"
                    : ""
                }`}
              >
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <i
                    className="ti ti-message-circle"
                    style={{
                      fontSize: "16px",
                      marginTop: "2px",
                      color: selectedSession?.id === session.id ? "#2563eb" : "#999",
                    }}
                  ></i>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {session.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {session.createdAt || "Just now"}
                    </p>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(session.id);
                  }}
                  className="ml-2 text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                  title="Delete chat"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col bg-white">
        {selectedSession && (
          <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-transparent">
            <h1 className="text-lg font-semibold text-gray-900">
              {selectedSession.title}
            </h1>
            <p className="text-xs text-gray-500 mt-1">
              Powered by AI • Document Search & Answers
            </p>
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div
                style={{
                  width: "56px",
                  height: "56px",
                  borderRadius: "50%",
                  background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: "16px",
                }}
              >
                <i className="ti ti-brain" style={{ fontSize: "28px", color: "white" }}></i>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Start asking questions
              </h2>
              <p className="text-gray-500 max-w-sm mb-6">
                Ask anything about your documents. I'll search and provide intelligent answers
                with sources.
              </p>
              <div className="grid grid-cols-2 gap-2">
                {["Document summary", "Key concepts", "Specific search", "Comparisons"].map(
                  (suggestion, i) => (
                    <button
                      key={i}
                      onClick={() => setInput(suggestion)}
                      className="px-3 py-2 text-xs text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      {suggestion}
                    </button>
                  )
                )}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} message-${msg.role}`}
              >
                <div className="flex gap-3 max-w-2xl">
                  {msg.role === "assistant" && (
                    <div
                      style={{
                        width: "32px",
                        height: "32px",
                        borderRadius: "50%",
                        background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      <i className="ti ti-brain" style={{ fontSize: "16px", color: "white" }}></i>
                    </div>
                  )}

                  <div
                    className={`px-4 py-3 rounded-2xl whitespace-pre-wrap text-sm leading-relaxed ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white rounded-br-none"
                        : "bg-gray-100 text-gray-900 rounded-bl-none border border-gray-200"
                    }`}
                  >
                    {msg.content}

                    {/* Sources panel — shown only on the last assistant message */}
                    {msg.role === "assistant" && hasSources &&
                      msg.id === messages.filter((m) => m.role === "assistant").at(-1)?.id && (
                      <div className="mt-4 border-t border-gray-300 pt-3 space-y-3">
                        <div className="text-xs font-semibold text-gray-600">Sources</div>

                        {sources.documents.length > 0 && (
                          <div>
                            <div className="text-xs text-gray-500 mb-1 font-medium">
                              Documents
                            </div>
                            {sources.documents.map((doc) => (
                              <div key={doc.id} className="mb-1">
                                <a
                                  href={doc.web_view_link}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-blue-600 text-xs hover:underline flex items-center gap-1"
                                >
                                  <span>📄</span>
                                  {doc.name}
                                </a>
                              </div>
                            ))}
                          </div>
                        )}

                        {sources.emails.length > 0 && (
                          <div>
                            <div className="text-xs text-gray-500 mb-1 font-medium">
                              Emails
                            </div>
                            {sources.emails.map((email) => (
  <div
    key={email.id}
    onClick={() => openEmail(email.id)}
    className="
      cursor-pointer
      hover:bg-gray-100
      rounded
      p-2
      mb-2
      text-xs
      flex
      items-start
      gap-2
    "
  >
    <span>✉️</span>

    <span>
      <span className="font-medium">
        {email.subject}
      </span>

      {" · "}

      <span className="text-gray-500">
        {email.sender}
      </span>
    </span>
  </div>
))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {msg.role === "user" && (
                    <div
                      style={{
                        width: "32px",
                        height: "32px",
                        borderRadius: "50%",
                        background: "#e5e7eb",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      <i className="ti ti-user" style={{ fontSize: "16px", color: "#6b7280" }}></i>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="flex justify-start message-assistant">
              <div className="flex gap-3">
                <div
                  style={{
                    width: "32px",
                    height: "32px",
                    borderRadius: "50%",
                    background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <i className="ti ti-brain" style={{ fontSize: "16px", color: "white" }}></i>
                </div>
                <div className="px-4 py-3 rounded-2xl bg-gray-100 rounded-bl-none border border-gray-200">
                  <div className="flex gap-2">
                    {[0, 0.2, 0.4].map((delay, i) => (
                      <div
                        key={i}
                        style={{
                          width: "8px",
                          height: "8px",
                          borderRadius: "50%",
                          background: "#9ca3af",
                          animation: `pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite ${delay}s`,
                        }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-gray-200 p-6 bg-white">
          <div className="flex gap-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              placeholder="Ask about your documents... (Shift+Enter for new line)"
              className="input-focus flex-1 border border-gray-300 rounded-lg px-4 py-3 text-sm outline-none placeholder-gray-500 resize-none"
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium flex items-center gap-2"
            >
              {loading ? (
                <i
                  className="ti ti-loader"
                  style={{ fontSize: "16px", animation: "spin 1s linear infinite" }}
                ></i>
              ) : (
                <i className="ti ti-send" style={{ fontSize: "16px" }}></i>
              )}
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2">Press Enter to send</p>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.5; }
          50% { opacity: 1; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
      {selectedEmail && (
  <EmailModal
    email={selectedEmail}
    onClose={() => setSelectedEmail(null)}
  />
)}
    </div>
  );
}