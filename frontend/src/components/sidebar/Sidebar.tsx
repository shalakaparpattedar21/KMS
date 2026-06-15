import { Link } from "react-router-dom";

export default function Sidebar() {

  const handleLogout = async () => {
    try {
      await fetch(
        "http://localhost:8000/api/auth/logout",
        {
          credentials: "include",
        }
      );

      window.location.href = "/";
    } catch (error) {
      console.error(error);
    }
  };

  const handleDisconnect = async () => {
    const confirmDisconnect = window.confirm(
      "Disconnect Google Drive and Gmail?"
    );

    if (!confirmDisconnect) return;

    try {
      await fetch(
        "http://localhost:8000/api/auth/disconnect",
        {
          method: "POST",
          credentials: "include",
        }
      );

      window.location.href = "/";
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className="w-56 bg-slate-900 text-white h-screen p-5 flex flex-col">

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
        <button
    onClick={handleLogout}
    className="bg-red-500 p-2 rounded"
  >
    Logout
  </button>

      <div className="mt-auto space-y-2">

      <button
        onClick={handleDisconnect}
        className="w-full py-2 rounded-lg bg-orange-500 hover:bg-orange-600"
      >
        Disconnect Google
      </button>

      <button
        onClick={handleLogout}
        className="w-full py-2 rounded-lg bg-red-500 hover:bg-red-600"
      >
        Logout
      </button>

    </div>
    </div>
  );
}