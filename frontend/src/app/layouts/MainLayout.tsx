import { Outlet } from "react-router-dom";
import TopNavbar from "../../components/navbar/TopNavbar";
import ActivityFeed from "../../components/activity/ActivityFeed";

export default function MainLayout() {
  return (
    <div className="h-screen flex flex-col">

      <TopNavbar />

      <div className="flex flex-1 overflow-hidden">

        <aside className="w-64 bg-white">
          <ActivityFeed />
        </aside>

        <main className="flex-1 bg-slate-100 p-6 overflow-y-auto">
          <Outlet />
        </main>

      </div>

    </div>
  );
}