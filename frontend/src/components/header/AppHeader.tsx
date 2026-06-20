export default function AppHeader() {
  return (
    <header className="mb-6 flex items-center justify-between rounded-lg border border-zinc-200 bg-white px-5 py-4 shadow-sm">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#A61E22]">
          RIIDL Enterprise
        </p>
        <h1 className="mt-1 text-2xl font-semibold text-zinc-950">
          Enterprise Knowledge Management System
        </h1>
        <p className="mt-1 text-sm text-zinc-500">AI-powered enterprise search</p>
      </div>
    </header>
  );
}
