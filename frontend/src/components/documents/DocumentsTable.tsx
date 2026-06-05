const documents = [
  {
    name: "API_Request_SOP.pdf",
    owner: "John",
    modified: "Today",
    type: "PDF",
  },
  {
    name: "HR_Policy.pdf",
    owner: "Sarah",
    modified: "Yesterday",
    type: "PDF",
  },
  {
    name: "Deployment_Guide.docx",
    owner: "Mike",
    modified: "Today",
    type: "DOCX",
  },
  {
    name: "Client_Onboarding.pdf",
    owner: "Shalaka",
    modified: "Today",
    type: "PDF",
  },
];

export default function DocumentsTable() {
  return (
    <div className="bg-white rounded-xl shadow p-5">
      <table className="w-full">
        <thead>
          <tr className="border-b">
            <th className="text-left py-3">Name</th>
            <th className="text-left py-3">Owner</th>
            <th className="text-left py-3">Modified</th>
            <th className="text-left py-3">Type</th>
          </tr>
        </thead>

        <tbody>
          {documents.map((doc) => (
            <tr
              key={doc.name}
              className="border-b hover:bg-slate-50"
            >
              <td className="py-3">{doc.name}</td>
              <td>{doc.owner}</td>
              <td>{doc.modified}</td>
              <td>{doc.type}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}