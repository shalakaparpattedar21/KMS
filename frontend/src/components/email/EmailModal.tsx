interface Props {
  email: any;
  onClose: () => void;
}

export default function EmailModal({
  email,
  onClose
}: Props) {

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
            className="px-4 py-2 bg-green-600 text-white rounded-lg"
          >
            Reply
          </button>

          <button
            className="px-4 py-2 bg-orange-500 text-white rounded-lg"
          >
            Forward
          </button>

        </div>

        <hr className="my-5"/>

        <div className="whitespace-pre-wrap text-sm">
          {email.body}
        </div>

      </div>

    </div>
  );
}