export default function SourcesPanel() {
  const sources = [
    "API_Request_SOP.pdf",
    "Deployment_Guide.pdf",
    "HR_Policy.pdf",
  ];

  return (
    <div className="bg-white rounded-xl shadow p-5">
      <h2 className="font-bold mb-3">
        Sources
      </h2>

      <div className="space-y-2">
        {sources.map((source) => (
          <div
            key={source}
            className="p-2 rounded bg-slate-50"
          >
            {source}
          </div>
        ))}
      </div>
    </div>
  );
}