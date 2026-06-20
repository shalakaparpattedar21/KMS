import { Outlet } from "react-router-dom";
import TopNavbar from "../../components/navbar/TopNavbar";

export default function MainLayout() {
  return (
    <div className="h-screen overflow-hidden bg-[#f6f5f4] text-zinc-950">
      <TopNavbar />

      <main className="h-[calc(100vh-72px)] overflow-y-auto bg-[#f6f5f4] p-4 kms-scrollbar md:p-6">
        <Outlet />
      </main>
    </div>
  );
}
