import { useEffect, useState, type ReactNode } from "react";
import { ExternalLink, File, FileSpreadsheet, FileText, Folder, Grid3X3, List, RefreshCw, Search } from "lucide-react";
import AppHeader from "../../components/header/AppHeader";
import { API_URL } from "../../services/api.ts";

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
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
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
  if (mimeType.includes("document") || mimeType.includes("word")) return "document";
  return "file";
};

const FileIcon = ({ type, size = 40 }: { type: string; size?: number }) => {
  const iconClass = "text-[#A61E22]";
  const iconProps = { size: Math.max(18, size * 0.46), className: iconClass };
  const icons: Record<string, ReactNode> = {
    folder: <Folder {...iconProps} />,
    spreadsheet: <FileSpreadsheet {...iconProps} />,
    pdf: <FileText {...iconProps} />,
    document: <FileText {...iconProps} />,
    file: <File {...iconProps} />,
  };

  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-lg border border-[#A61E22]/10 bg-[#A61E22]/8"
      style={{ width: size, height: size }}
    >
      {icons[type] || icons.file}
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
      const res = await fetch(`${API_URL}/api/documents/`, { credentials: "include" });
      const data = await res.json();
      setFiles(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    let active = true;

    const loadInitialDocuments = async () => {
      try {
        const res = await fetch(`${API_URL}/api/documents/`, { credentials: "include" });
        const data = await res.json();
        if (active) {
          setFiles(Array.isArray(data) ? data : []);
        }
      } catch (error) {
        console.error(error);
      }
    };

    loadInitialDocuments();

    return () => {
      active = false;
    };
  }, []);

  const handleSync = async () => {
    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/api/sync/start`, {
        method: "POST",
        credentials: "include",
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Please connect a Google account first.");
        return;
      }

      await fetchDocuments();

    } catch (error) {
      console.error(error);
      alert("Sync failed");
    } finally {
      setLoading(false);
    }
  };

  const filteredFiles = [...files]
    .filter((file) => file.name.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      if (sortBy === "name") return a.name.localeCompare(b.name);
      if (sortBy === "size") return (b.size || 0) - (a.size || 0);
      return 0;
    });

  const docsCount = files.filter((f) => f.mime_type.includes("google-apps.document")).length;
  const foldersCount = files.filter((f) => f.mime_type.includes("folder")).length;
  const gridColumns = { small: "grid-cols-2 sm:grid-cols-4 lg:grid-cols-7", medium: "grid-cols-1 sm:grid-cols-3 lg:grid-cols-5", large: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" }[gridSize];
  const iconSize = { small: 34, medium: 48, large: 64 }[gridSize];

  return (
    <>
      <AppHeader />

      <div className="space-y-6">
        <section className="flex flex-col gap-4 rounded-lg border border-zinc-200 bg-white p-5 shadow-sm lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#A61E22]">
              Document Discovery
            </p>
            <h2 className="mt-1 text-2xl font-semibold text-zinc-950">Drive Documents</h2>
            <p className="mt-1 text-sm text-zinc-500">Browse, sync, and open files connected from Google Drive.</p>
          </div>

          <button
            onClick={handleSync}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#A61E22] px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-[#A61E22]/15 transition hover:bg-[#8f181c] disabled:opacity-50"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            {loading ? "Syncing..." : "Sync Now"}
          </button>
        </section>

        <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {[
            ["Total Files", files.length],
            ["Google Docs", docsCount],
            ["Folders", foldersCount],
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
              <p className="text-sm font-medium text-zinc-500">{label}</p>
              <h3 className="mt-2 text-3xl font-semibold text-zinc-950">{value}</h3>
            </div>
          ))}
        </section>

        <section className="flex flex-col gap-3 rounded-lg border border-zinc-200 bg-white p-4 shadow-sm lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
            <input
              type="text"
              placeholder="Search documents..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="kms-focus w-full rounded-lg border border-zinc-200 bg-zinc-50 py-3 pl-10 pr-4 text-sm text-zinc-900 placeholder:text-zinc-400"
            />
          </div>

          <div className="flex shrink-0 gap-2">
            <div className="flex rounded-lg border border-zinc-200 bg-zinc-50 p-1">
              <button
                onClick={() => setViewMode("table")}
                title="List view"
                className={`flex h-9 w-9 items-center justify-center rounded-md transition ${viewMode === "table" ? "bg-white text-[#A61E22] shadow-sm" : "text-zinc-500 hover:text-zinc-950"}`}
              >
                <List size={17} />
              </button>
              <button
                onClick={() => setViewMode("grid")}
                title="Grid view"
                className={`flex h-9 w-9 items-center justify-center rounded-md transition ${viewMode === "grid" ? "bg-white text-[#A61E22] shadow-sm" : "text-zinc-500 hover:text-zinc-950"}`}
              >
                <Grid3X3 size={17} />
              </button>
            </div>

            {viewMode === "grid" && (
              <div className="flex rounded-lg border border-zinc-200 bg-zinc-50 p-1">
                {(["small", "medium", "large"] as const).map((size) => (
                  <button
                    key={size}
                    onClick={() => setGridSize(size)}
                    className={`h-9 rounded-md px-3 text-xs font-semibold uppercase transition ${gridSize === size ? "bg-white text-[#A61E22] shadow-sm" : "text-zinc-500 hover:text-zinc-950"}`}
                  >
                    {size[0]}
                  </button>
                ))}
              </div>
            )}
          </div>
        </section>

        <section className="rounded-lg border border-zinc-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-4">
            <div>
              <h3 className="text-base font-semibold text-zinc-950">Search Results</h3>
              <p className="text-sm text-zinc-500">{filteredFiles.length} visible documents</p>
            </div>
          </div>

          {filteredFiles.length === 0 ? (
            <div className="flex min-h-72 flex-col items-center justify-center p-8 text-center">
              <FileText size={36} className="mb-3 text-zinc-300" />
              <h4 className="text-base font-semibold text-zinc-900">No documents found</h4>
              <p className="mt-2 max-w-sm text-sm text-zinc-500">Try a different search term or sync Drive again.</p>
            </div>
          ) : viewMode === "table" ? (
            <div className="overflow-x-auto kms-scrollbar">
              <table className="w-full min-w-[900px] text-left text-sm">
                <thead className="bg-zinc-50 text-xs font-semibold uppercase tracking-[0.12em] text-zinc-500">
                  <tr>
                    <th className="px-5 py-3 cursor-pointer" onClick={() => setSortBy("name")}>Name</th>
                    <th className="px-5 py-3">Type</th>
                    <th className="px-5 py-3 cursor-pointer" onClick={() => setSortBy("size")}>Size</th>
                    <th className="px-5 py-3">Modified</th>
                    <th className="px-5 py-3">Owner</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100">
                  {filteredFiles.map((file) => (
                    <tr key={file.id} className="transition hover:bg-[#A61E22]/[0.025]">
                      <td className="px-5 py-4">
                        <div className="flex min-w-0 items-center gap-3">
                          <FileIcon type={getFileIcon(file.mime_type)} size={38} />
                          <span className="truncate font-medium text-zinc-950">{file.name}</span>
                        </div>
                      </td>
                      <td className="max-w-xs truncate px-5 py-4 text-zinc-500">{file.mime_type}</td>
                      <td className="px-5 py-4 text-zinc-700">{formatSize(file.size)}</td>
                      <td className="px-5 py-4 text-zinc-700">{formatDate(file.modified_time)}</td>
                      <td className="max-w-[180px] truncate px-5 py-4 text-zinc-600">{file.owner_email || "-"}</td>
                      <td className="px-5 py-4">
                        <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                          {file.sync_status || "synced"}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        {file.web_view_link ? (
                          <a
                            href={file.web_view_link}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs font-semibold text-zinc-800 transition hover:border-[#A61E22]/30 hover:text-[#A61E22]"
                          >
                            View <ExternalLink size={14} />
                          </a>
                        ) : (
                          <span className="text-zinc-400">N/A</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className={`grid gap-3 p-5 ${gridColumns}`}>
              {filteredFiles.map((file) => (
                <div
                  key={file.id}
                  className="group flex min-w-0 flex-col gap-3 rounded-lg border border-zinc-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-[#A61E22]/25 hover:shadow-lg hover:shadow-zinc-950/5"
                >
                  <FileIcon type={getFileIcon(file.mime_type)} size={iconSize} />
                  <div className="min-w-0">
                    <h4 className="truncate text-sm font-semibold text-zinc-950">{file.name}</h4>
                    {gridSize !== "small" && (
                      <p className="mt-1 text-xs text-zinc-500">{formatSize(file.size)} - {formatDate(file.modified_time)}</p>
                    )}
                  </div>
                  {gridSize === "large" && file.web_view_link && (
                    <a
                      href={file.web_view_link}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-auto inline-flex items-center justify-center gap-2 rounded-lg bg-zinc-950 px-3 py-2 text-sm font-semibold text-white transition hover:bg-[#A61E22]"
                    >
                      Open <ExternalLink size={14} />
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </>
  );
}
