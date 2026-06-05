import { Link } from "react-router-dom";

export default function Sidebar() {
  return (
    <div className="w-56 bg-slate-900 text-white h-screen p-5">
      <h1 className="text-2xl font-bold mb-8">
        Enterprise KMS
      </h1>

      <nav className="flex flex-col gap-4">
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/search">AI Search</Link>
        <Link to="/documents">Documents</Link>
        <Link to="/users">Users</Link>
        <Link to="/activity">Activity</Link>
        <Link to="/settings">Settings</Link>
      </nav>
    </div>
  );
}