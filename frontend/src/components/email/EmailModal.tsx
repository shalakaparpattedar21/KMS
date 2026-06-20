import { useState } from "react";

interface Props {
  email: any;
  onClose: () => void;
}

export default function EmailModal({
  email,
  onClose
}: Props) {

  const [showReply, setShowReply] =
  useState(false);

const [showForward, setShowForward] =
  useState(false);

const [replyText, setReplyText] =
  useState("");

const [forwardTo, setForwardTo] =
  useState("");

const [forwardText, setForwardText] =
  useState("");

  const sendReply = async () => {

  const response = await fetch(
    "http://localhost:8000/api/gmail/actions/reply",
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message_id:
          email.gmail_message_id,

        thread_id:
          email.gmail_thread_id,

        content:
          replyText
      })
    }
  );

  const data = await response.json();

console.log(data);

if (data.id) {
  alert("Reply Sent Successfully");
  setShowReply(false);
} else {
  alert(
    JSON.stringify(data)
  );
}
  };
const sendForward = async () => {

  const response = await fetch(
    "http://localhost:8000/api/gmail/actions/forward",
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message_id:
          email.gmail_message_id,

        recipient:
          forwardTo,

        content:
          forwardText
      })
    }
  );

  const data = await response.json();

console.log(data);

if (data.id) {
  alert("Forwarded Successfully");
  setShowForward(false);
} else {
  alert(
    JSON.stringify(data)
  );
}
};
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">

      <div className="bg-white w-[900px] max-h-[90vh] overflow-y-auto rounded-xl p-6 shadow-xl">

        <div className="flex justify-between items-center mb-4">

          <h2 className="text-xl font-bold">
            {email.subject}
          </h2>

          <button
            onClick={onClose}
            className="text-gray-500 hover:text-red-500"
          >
            ✕
          </button>

        </div>

        <div className="space-y-2 text-sm">

          <div>
            <strong>From:</strong> {email.sender}
          </div>

          <div>
            <strong>To:</strong> {email.recipient}
          </div>

          <div>
            <strong>Date:</strong> {email.received_at}
          </div>

        </div>

        <div className="flex gap-3 mt-5">

          <a
            href={`https://mail.google.com/mail/u/0/#inbox/${email.gmail_message_id}`}
            target="_blank"
            rel="noreferrer"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg"
          >
            Open Gmail
          </a>

              <button
          onClick={() =>
            setShowReply(true)
          }
          className="px-4 py-2 bg-green-600 text-white rounded-lg"
        >
          Reply
        </button>
          <button onClick={() =>setShowForward(true)} className="px-4 py-2 bg-orange-500 text-white rounded-lg">
                Forward
          </button>

        </div>

        <hr className="my-5"/>

        <div className="whitespace-pre-wrap text-sm">
          {email.body}
        </div>
        {
  showReply && (
    <div className="mt-6 border rounded-lg p-4">

      <h3 className="font-semibold mb-2">
        Reply
      </h3>

      <textarea
        value={replyText}
        onChange={(e) =>
          setReplyText(
            e.target.value
          )
        }
        className="w-full border rounded p-2 h-32"
      />

      <div className="mt-3 flex gap-2">

        <button
          onClick={sendReply}
          className="bg-green-600 text-white px-4 py-2 rounded"
        >
          Send Reply
        </button>

        <button
          onClick={() =>
            setShowReply(false)
          }
          className="border px-4 py-2 rounded"
        >
          Cancel
        </button>

      </div>

    </div>
  )
}
{
  showForward && (
    <div className="mt-6 border rounded-lg p-4">

      <h3 className="font-semibold mb-2">
        Forward Email
      </h3>

      <input
        type="email"
        placeholder="Recipient Email"
        value={forwardTo}
        onChange={(e) =>
          setForwardTo(
            e.target.value
          )
        }
        className="w-full border rounded p-2 mb-3"
      />

      <textarea
        value={forwardText}
        onChange={(e) =>
          setForwardText(
            e.target.value
          )
        }
        className="w-full border rounded p-2 h-32"
        placeholder="Optional message"
      />

      <div className="mt-3 flex gap-2">

        <button
          onClick={sendForward}
          className="bg-orange-500 text-white px-4 py-2 rounded"
        >
          Forward
        </button>

        <button
          onClick={() =>
            setShowForward(false)
          }
          className="border px-4 py-2 rounded"
        >
          Cancel
        </button>

      </div>

    </div>
  )
}


      </div>

    </div>
  );
}
