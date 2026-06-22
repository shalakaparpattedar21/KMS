import { ArrowRight, Mail, FileText, Sparkles, ShieldCheck, Lock } from "lucide-react";

const features = [
  {
    icon: Mail,
    title: "Email Intelligence",
    description: "Find conversations instantly, summarize long threads, draft responses and take actions directly from AI search.",
  },
  {
    icon: FileText,
    title: "Document Discovery",
    description: "Locate relevant documents using semantic search, not just filenames or keywords.",
  },
  {
    icon: Sparkles,
    title: "Knowledge Hub",
    description: "Bring together emails, documents and organizational knowledge into a single searchable workspace.",
  },
  {
    icon: ArrowRight,
    title: "AI Assistant",
    description: "Ask questions in natural language and receive answers backed by verified organizational sources.",
  },
];

export default function Login() {
  const login = () => {
    window.location.href = "http://localhost:8000/api/auth/google/login";
  };

  return (
    <main className="min-h-screen overflow-hidden bg-[#f7f6f4] text-[#111113]">
      {/* Red Corner Gradients */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-gradient-to-br from-[#A61E22]/40 to-[#A61E22]/5 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-gradient-to-tl from-[#A61E22]/15 to-[#A61E22]/5 blur-3xl" />
        <div className="absolute top-1/2 -right-32 h-80 w-80 rounded-full bg-gradient-to-l from-[#A61E22]/25 to-transparent blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative z-10 mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-6 lg:px-8">
        <div className="flex items-center gap-4">
          <img
            src="/riidl_logo.png"
            alt="RIIDL"
            className="h-12 w-auto"
          />
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[#A61E22]">
              Enterprise
            </p>
            <h1 className="text-base font-semibold text-zinc-950">Knowledge Platform</h1>
          </div>
        </div>
        <div className="hidden items-center gap-2 rounded-full border border-[#A61E22]/20 bg-white/60 px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm backdrop-blur md:flex hover:border-[#A61E22]/40 transition-colors">
          <ShieldCheck size={16} className="text-[#A61E22]" />
          Enterprise-ready
        </div>
      </header>

      {/* Main Section */}
      <section className="relative z-10 mx-auto w-full max-w-7xl px-6 py-8 lg:px-8 lg:py-12">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.2fr_0.8fr] lg:gap-12 items-start">
          {/* Left Column - Hero Content */}
          <div className="space-y-8">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 rounded-full border border-[#A61E22]/20 bg-white/70 px-3.5 py-2 text-sm font-medium text-[#A61E22] shadow-sm backdrop-blur hover:border-[#A61E22]/40 transition-all">
              <Sparkles size={16} />
              Accessing Data across RIIDL
            </div>

            {/* Headline */}
            <div className="space-y-4">
              <h2 className="max-w-3xl text-5xl font-bold leading-tight text-zinc-950 sm:text-6xl lg:text-6xl">
                AI-Powered Knowledge Retrieval System
              </h2>
              <p className="max-w-2xl text-lg leading-relaxed text-zinc-600">
                Search emails, documents and institutional knowledge through semantic retrieval and source-backed answers.
              </p>
            </div>

            {/* Benefit Points */}
            <ul className="space-y-3 max-w-2xl">
              <li className="flex items-start gap-3 text-zinc-700">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#A61E22]/10 mt-0.5">
                  <span className="h-2 w-2 rounded-full bg-[#A61E22]" />
                </span>
                <span>Connect Gmail and Google Drive for unified access</span>
              </li>
              <li className="flex items-start gap-3 text-zinc-700">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#A61E22]/10 mt-0.5">
                  <span className="h-2 w-2 rounded-full bg-[#A61E22]" />
                </span>
                <span>Search organizational knowledge using natural language</span>
              </li>
              <li className="flex items-start gap-3 text-zinc-700">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#A61E22]/10 mt-0.5">
                  <span className="h-2 w-2 rounded-full bg-[#A61E22]" />
                </span>
                <span>Get source-backed answers instantly with verified context</span>
              </li>
            </ul>

            {/* Feature Grid */}
            <div className="grid max-w-4xl grid-cols-1 gap-4 sm:grid-cols-2 pt-4">
              {features.map((feature) => {
                const Icon = feature.icon;
                return (
                  <div
                    key={feature.title}
                    className="group rounded-xl border border-zinc-200 bg-white/70 p-5 shadow-sm backdrop-blur transition duration-300 hover:border-[#A61E22]/30 hover:shadow-lg hover:shadow-[#A61E22]/10 hover:-translate-y-1"
                  >
                    <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-[#A61E22]/10 text-[#A61E22] transition-colors group-hover:bg-[#A61E22] group-hover:text-white">
                      <Icon size={20} />
                    </div>
                    <h3 className="text-sm font-semibold text-zinc-950">{feature.title}</h3>
                    <p className="mt-1.5 text-xs leading-5 text-zinc-600">{feature.description}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column - Sign In Card (Beside Title) */}
          <div className="lg:sticky lg:top-8">
            <div className="rounded-2xl border border-zinc-200 bg-white/80 p-3 shadow-2xl shadow-zinc-950/15 backdrop-blur">
              <div className="rounded-xl border border-zinc-100 bg-gradient-to-b from-white via-zinc-50/50 to-zinc-50 p-8 space-y-6">
                {/* Card Header */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Lock size={18} className="text-[#A61E22]" />
                    <p className="text-xs font-semibold uppercase tracking-wider text-[#A61E22]">Secure Sign In</p>
                  </div>
                  <h3 className="text-2xl font-bold text-zinc-950">Access Enterprise Intelligence</h3>
                  <p className="text-sm leading-relaxed text-zinc-600">
                    Securely connect your Google account to explore organizational knowledge across Gmail, Drive and AI-powered search.
                  </p>
                </div>

                {/* Sign In Button */}
                <button
                  onClick={login}
                  className="group relative w-full overflow-hidden rounded-lg bg-[#A61E22] px-6 py-4 text-sm font-semibold text-white shadow-lg shadow-[#A61E22]/25 transition-all duration-200 hover:bg-[#8f181c] hover:shadow-xl hover:shadow-[#A61E22]/30 active:scale-95"
                >
                  <span className="relative flex items-center justify-between">
                    <span className="flex items-center gap-3">
                      <span className="flex h-7 w-7 items-center justify-center rounded-md bg-white text-xs font-bold text-[#A61E22]">
                        G
                      </span>
                      Sign in with Google
                    </span>
                    <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
                  </span>
                </button>

                {/* Features List */}
                <div className="space-y-2 pt-2 border-t border-zinc-100">
                  {["Gmail Search", "Document Search", "Knowledge Hub"].map((item) => (
                    <div key={item} className="flex items-center gap-2 text-xs text-zinc-600">
                      <div className="h-1.5 w-1.5 rounded-full bg-[#A61E22]/40" />
                      {item}
                    </div>
                  ))}
                </div>

                {/* Trust Badges */}
                <div className="pt-2 border-t border-zinc-100 space-y-2">
                  <div className="flex items-center gap-2 text-xs text-zinc-500">
                    <ShieldCheck size={14} className="text-[#A61E22]" />
                    Enterprise-grade security
                  </div>
                  <div className="flex items-center gap-2 text-xs text-zinc-500">
                    <Lock size={14} className="text-[#A61E22]" />
                    OAuth 2.0 encrypted
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}