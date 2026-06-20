import { useState } from "react";
import { CalendarDays, ExternalLink, Forward, Mail, Reply, Send, UserRound, X } from "lucide-react";

interface EmailDetails {
  subject: string;
  sender: string;
  recipient: string;
  received_at: string;
  body: string;
  gmail_message_id: string;
  gmail_thread_id: string;
}

interface Props {
  email: EmailDetails;
  onClose: () => void;
}

export default function EmailModal({ email, onClose }: Props) {
  const [showReply, setShowReply] = useState(false);
  const [showForward, setShowForward] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [forwardTo, setForwardTo] = useState("");
  const [forwardText, setForwardText] = useState("");

  const sendReply = async () => {
    const response = await fetch("http://localhost:8000/api/gmail/actions/reply", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message_id: email.gmail_message_id,
        thread_id: email.gmail_thread_id,
        content: replyText,
      }),
    });

    const data = await response.json();

    console.log(data);

    if (data.id) {
      alert("Reply Sent Successfully");
      setShowReply(false);
    } else {
      alert(JSON.stringify(data));
    }
  };

  const sendForward = async () => {
    const response = await fetch("http://localhost:8000/api/gmail/actions/forward", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message_id: email.gmail_message_id,
        recipient: forwardTo,
        content: forwardText,
      }),
    });

    const data = await response.json();

    console.log(data);

    if (data.id) {
      alert("Forwarded Successfully");
      setShowForward(false);
    } else {
      alert(JSON.stringify(data));
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/55 p-4 backdrop-blur-sm">
      <div className="flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-2xl shadow-zinc-950/25">
        <header className="border-b border-zinc-200 bg-gradient-to-b from-white to-zinc-50 px-6 py-5">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#A61E22]">
                <Mail size={15} />
                Gmail source
              </div>
              <h2 className="text-2xl font-semibold leading-tight text-zinc-950">{email.subject}</h2>
            </div>

            <button
              onClick={onClose}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-zinc-200 bg-white text-zinc-500 transition hover:border-[#A61E22]/30 hover:text-[#A61E22]"
              title="Close"
            >
              <X size={18} />
            </button>
          </div>

          <div className="mt-5 grid grid-cols-1 gap-3 text-sm md:grid-cols-3">
            <div className="rounded-lg border border-zinc-200 bg-white p-3">
              <p className="mb-1 flex items-center gap-2 text-xs font-medium text-zinc-500">
                <UserRound size={14} /> From
              </p>
              <p className="truncate font-medium text-zinc-900">{email.sender}</p>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white p-3">
              <p className="mb-1 flex items-center gap-2 text-xs font-medium text-zinc-500">
                <Mail size={14} /> To
              </p>
              <p className="truncate font-medium text-zinc-900">{email.recipient}</p>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white p-3">
              <p className="mb-1 flex items-center gap-2 text-xs font-medium text-zinc-500">
                <CalendarDays size={14} /> Date
              </p>
              <p className="truncate font-medium text-zinc-900">{email.received_at}</p>
            </div>
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            <a
              href={`https://mail.google.com/mail/u/0/#inbox/${email.gmail_message_id}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg bg-zinc-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-zinc-800"
            >
              <ExternalLink size={16} />
              Open Gmail
            </a>

            <button
              onClick={() => setShowReply(true)}
              className="inline-flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2.5 text-sm font-semibold text-zinc-800 transition hover:border-[#A61E22]/30 hover:text-[#A61E22]"
            >
              <Reply size={16} />
              Reply
            </button>
            <button
              onClick={() => setShowForward(true)}
              className="inline-flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2.5 text-sm font-semibold text-zinc-800 transition hover:border-[#A61E22]/30 hover:text-[#A61E22]"
            >
              <Forward size={16} />
              Forward
            </button>
          </div>
        </header>

        <div className="overflow-y-auto p-6 kms-scrollbar">
          <article className="rounded-lg border border-zinc-200 bg-[#fbfaf9] p-5 text-sm leading-7 text-zinc-800">
            <div className="whitespace-pre-wrap">{email.body}</div>
          </article>

          {showReply && (
            <section className="mt-5 rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-zinc-950">
                <Reply size={16} className="text-[#A61E22]" />
                Reply
              </h3>

              <textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                className="kms-focus h-32 w-full resize-none rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-900 placeholder:text-zinc-400"
                placeholder="Write your reply..."
              />

              <div className="mt-3 flex gap-2">
                <button
                  onClick={sendReply}
                  className="inline-flex items-center gap-2 rounded-lg bg-[#A61E22] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#8f181c]"
                >
                  <Send size={15} />
                  Send Reply
                </button>

                <button
                  onClick={() => setShowReply(false)}
                  className="rounded-lg border border-zinc-200 px-4 py-2 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-50"
                >
                  Cancel
                </button>
              </div>
            </section>
          )}

          {showForward && (
            <section className="mt-5 rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-zinc-950">
                <Forward size={16} className="text-[#A61E22]" />
                Forward Email
              </h3>

              <input
                type="email"
                placeholder="Recipient email"
                value={forwardTo}
                onChange={(e) => setForwardTo(e.target.value)}
                className="kms-focus mb-3 w-full rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-900 placeholder:text-zinc-400"
              />

              <textarea
                value={forwardText}
                onChange={(e) => setForwardText(e.target.value)}
                className="kms-focus h-32 w-full resize-none rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-900 placeholder:text-zinc-400"
                placeholder="Optional message"
              />

              <div className="mt-3 flex gap-2">
                <button
                  onClick={sendForward}
                  className="inline-flex items-center gap-2 rounded-lg bg-[#A61E22] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#8f181c]"
                >
                  <Send size={15} />
                  Forward
                </button>

                <button
                  onClick={() => setShowForward(false)}
                  className="rounded-lg border border-zinc-200 px-4 py-2 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-50"
                >
                  Cancel
                </button>
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

