import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

export default function DocumentPreview() {
  const { id } = useParams();

  const [document, setDocument] = useState<any>(null);

  useEffect(() => {
    fetch(
      `http://localhost:8000/api/documents/preview/${id}`
    )
      .then((res) => res.json())
      .then((data) => setDocument(data));
  }, [id]);

  if (!document) {
    return <div>Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow p-6">
        <h1 className="text-3xl font-bold">
          {document.name}
        </h1>
      </div>

      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="font-semibold mb-4">
          Document Content
        </h2>

        <pre className="whitespace-pre-wrap">
          {document.preview}
        </pre>
      </div>
    </div>
  );
}