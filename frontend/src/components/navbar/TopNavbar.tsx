import { Link, useLocation } from "react-router-dom";

export default function TopNavbar() {
  const location = useLocation();

  const navItems = [
    { label: "AI Search", path: "/search" },
    { label: "Documents", path: "/documents" },
    
  ];
  return (
    <header className="h-16 bg-slate-900 text-white border-b border-slate-800">
      <div className="h-full flex items-center justify-between px-8">

        <div className="flex items-center gap-10">
          <h1 className="font-bold text-xl">
            Enterprise KMS
          </h1>

          <nav className="flex items-center gap-6">

            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`transition-colors ${
                  location.pathname === item.path
                    ? "text-blue-400 font-medium"
                    : "text-gray-300 hover:text-white"
                }`}
              >
                {item.label}
              </Link>
            ))}

          </nav>
        </div>

        <div className="flex items-center gap-3">
         

          <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center">
            S
          </div>
        </div>

      </div>
    </header>
  );
}