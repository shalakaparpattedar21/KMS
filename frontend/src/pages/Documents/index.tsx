import { useEffect, useState } from "react";
import AppHeader from "../../components/header/AppHeader";

interface DriveFile {
  id: number;
  drive_file_id: string;
  name: string;
  mime_type: string;
  owner_email?: string;
  size?: number;
  sync_status?: string;
  web_view_link?: string;
  modified_time?: string;
}

const formatSize = (bytes?: number) => {
  if (!bytes) return "-";

  const kb = bytes / 1024;

  if (kb < 1024) {
    return `${kb.toFixed(1)} KB`;
  }

  const mb = kb / 1024;

  return `${mb.toFixed(1)} MB`;
};

const formatDate = (date?: string) => {
  if (!date) return "-";

  return new Date(date).toLocaleDateString();
};

const getFileIcon = (mimeType: string) => {
  if (mimeType.includes("folder")) return "folder";
  if (mimeType.includes("spreadsheet") || mimeType.includes("excel")) return "spreadsheet";
  if (mimeType.includes("pdf")) return "pdf";
  if (mimeType.includes("image")) return "image";
  if (mimeType.includes("video")) return "video";
  if (mimeType.includes("document") || mimeType.includes("word")) return "document";
  return "file";
};

const FileIcon = ({ type, size = 40 }: { type: string; size?: number }) => {
  const icons: Record<string, { bg: string; color: string; label: string }> = {
    folder:      { bg: "#FEF3C7", color: "#D97706", label: "DIR" },
    spreadsheet: { bg: "#D1FAE5", color: "#059669", label: "XLS" },
    pdf:         { bg: "#FEE2E2", color: "#DC2626", label: "PDF" },
    image:       { bg: "#EDE9FE", color: "#7C3AED", label: "IMG" },
    video:       { bg: "#DBEAFE", color: "#2563EB", label: "VID" },
    document:    { bg: "#DBEAFE", color: "#2563EB", label: "DOC" },
    file:        { bg: "#F3F4F6", color: "#6B7280", label: "FILE" },
  };

  const { bg, color, label } = icons[type] || icons.file;

  return (
    <div
      style={{
        width: size,
        height: size,
        background: bg,
        borderRadius: 8,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontWeight: 700,
        fontSize: size * 0.28,
        color,
        letterSpacing: "0.03em",
        flexShrink: 0,
      }}
    >
      {label}
    </div>
  );
};

export default function Documents() {
  const [files, setFiles] = useState<DriveFile[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState("name");
  const [viewMode, setViewMode] = useState<"table" | "grid">("table");
  const [gridSize, setGridSize] = useState<"small" | "medium" | "large">("medium");

  const fetchDocuments = async () => {
    try {
      const res = await fetch(
        "http://localhost:8000/api/documents/",
        {
          credentials: "include",
        }
      );

      const data = await res.json();

      setFiles(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleSync = async () => {
    try {
      setLoading(true);

      await fetch(
        "http://localhost:8000/api/sync/start",
        {
          method: "POST",
          credentials: "include",
        }
      );

      await fetchDocuments();
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const filteredFiles = [...files]
    .filter((file) =>
      file.name.toLowerCase().includes(search.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === "name") {
        return a.name.localeCompare(b.name);
      }

      if (sortBy === "size") {
        return (b.size || 0) - (a.size || 0);
      }

      return 0;
    });

  return (
    <>
      <AppHeader />

      <div className="space-y-6">

        {/* Header */}
        <div className="bg-white rounded-xl shadow p-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">
              Documents
            </h2>

            <p className="text-gray-500 mt-1">
              Browse and search files synced from Google Drive
            </p>
          </div>

          <button
            onClick={handleSync}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Syncing..." : "Sync Now"}
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">

          <div className="bg-white rounded-xl shadow p-4">
            <p className="text-gray-500 text-sm">
              Total Files
            </p>

            <h3 className="text-2xl font-bold">
              {files.length}
            </h3>
          </div>

          <div className="bg-white rounded-xl shadow p-4">
            <p className="text-gray-500 text-sm">
              Google Docs
            </p>

            <h3 className="text-2xl font-bold">
              {
                files.filter((f) =>
                  f.mime_type.includes(
                    "google-apps.document"
                  )
                ).length
              }
            </h3>
          </div>

          <div className="bg-white rounded-xl shadow p-4">
            <p className="text-gray-500 text-sm">
              Folders
            </p>

            <h3 className="text-2xl font-bold">
              {
                files.filter((f) =>
                  f.mime_type.includes("folder")
                ).length
              }
            </h3>
          </div>

        </div>

        {/* Search + View Controls */}
        <div className="bg-white rounded-xl shadow p-4 flex gap-4 items-center">

          <input
            type="text"
            placeholder="Search documents..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 border rounded-lg p-3 outline-none"
          />

          {/* View mode toggle */}
          <div className="flex gap-1 border rounded-lg p-1">

            <button
              onClick={() => setViewMode("table")}
              title="List view"
              className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                viewMode === "table"
                  ? "bg-blue-600 text-white"
                  : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              List
            </button>

            <button
              onClick={() => setViewMode("grid")}
              title="Grid view"
              className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                viewMode === "grid"
                  ? "bg-blue-600 text-white"
                  : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              Grid
            </button>

          </div>

          {/* Grid size toggle — only shown in grid mode */}
          {viewMode === "grid" && (
            <div className="flex gap-1 border rounded-lg p-1">

              <button
                onClick={() => setGridSize("small")}
                title="Small icons"
                className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                  gridSize === "small"
                    ? "bg-gray-700 text-white"
                    : "text-gray-500 hover:bg-gray-100"
                }`}
              >
                S
              </button>

              <button
                onClick={() => setGridSize("medium")}
                title="Medium icons"
                className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                  gridSize === "medium"
                    ? "bg-gray-700 text-white"
                    : "text-gray-500 hover:bg-gray-100"
                }`}
              >
                M
              </button>

              <button
                onClick={() => setGridSize("large")}
                title="Large icons"
                className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                  gridSize === "large"
                    ? "bg-gray-700 text-white"
                    : "text-gray-500 hover:bg-gray-100"
                }`}
              >
                L
              </button>

            </div>
          )}

        </div>

        {/* Documents Table */}
        <div className="bg-white rounded-xl shadow p-6">

          <h3 className="font-semibold text-lg mb-4">
            Drive Documents
          </h3>

          {viewMode === "table" ? (

            <div className="overflow-x-auto">

              <table className="w-full">

              <thead>
                <tr className="border-b text-left bg-gray-50">

                  <th
                    className="p-3 cursor-pointer"
                    onClick={() => setSortBy("name")}
                  >
                    Name ↑↓
                  </th>

                  <th className="p-3">
                    Type
                  </th>

                  <th
                    className="p-3 cursor-pointer"
                    onClick={() => setSortBy("size")}
                  >
                    Size ↑↓
                  </th>

                  <th className="p-3">
                    Modified
                  </th>

                  <th className="p-3">
                    Owner
                  </th>

                  <th className="p-3">
                    Status
                  </th>

                  <th className="p-3">
                    Actions
                  </th>

                </tr>
              </thead>

              <tbody>

                {filteredFiles.map((file) => (

                  <tr
                    key={file.id}
                    className="border-b hover:bg-gray-50"
                  >

                    <td className="p-3 font-medium">
                      {file.name}
                    </td>

                    <td className="p-3 text-gray-600">
                      {file.mime_type}
                    </td>

                    <td className="p-3">
                      {formatSize(file.size)}
                    </td>

                    <td className="p-3">
                      {formatDate(file.modified_time)}
                    </td>

                    <td className="p-3">
                      {file.owner_email || "-"}
                    </td>

                    <td className="p-3">

                      <span
                        className="
                          px-2
                          py-1
                          rounded-full
                          text-sm
                          bg-green-100
                          text-green-700
                        "
                      >
                        {file.sync_status || "synced"}
                      </span>

                    </td>

                    <td className="p-3">

                      {file.web_view_link ? (
                        <a
                          href={file.web_view_link}
                          target="_blank"
                          rel="noreferrer"
                          className="
                            bg-blue-600
                            text-white
                            px-3
                            py-2
                            rounded-lg
                            hover:bg-blue-700
                          "
                        >
                          View
                        </a>
                      ) : (
                        <span className="text-gray-400">
                          N/A
                        </span>
                      )}

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

            </div>

          ) : (

            (() => {
              const cols = { small: 7, medium: 5, large: 3 }[gridSize];
              const iconSize = { small: 32, medium: 48, large: 64 }[gridSize];
              const textSize = { small: "text-xs", medium: "text-sm", large: "text-base" }[gridSize];

              return (
                <div
                  className="grid gap-3"
                  style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
                >

                  {filteredFiles.map((file) => (

                    <div
                      key={file.id}
                      className="border rounded-xl p-3 hover:shadow-md transition cursor-pointer flex flex-col gap-2"
                    >

                      <FileIcon
                        type={getFileIcon(file.mime_type)}
                        size={iconSize}
                      />

                      <h4 className={`font-medium truncate ${textSize}`}>
                        {file.name}
                      </h4>

                      {gridSize !== "small" && (
                        <>
                          <p className="text-xs text-gray-500">
                            {formatSize(file.size)}
                          </p>

                          <p className="text-xs text-gray-400">
                            {formatDate(file.modified_time)}
                          </p>
                        </>
                      )}

                      {gridSize === "large" && file.web_view_link && (
                        <a
                          href={file.web_view_link}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-1 bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm text-center hover:bg-blue-700"
                        >
                          Open
                        </a>
                      )}

                    </div>

                  ))}

                </div>
              );
            })()

          )}

        </div>

      </div>
    </>
  );
}