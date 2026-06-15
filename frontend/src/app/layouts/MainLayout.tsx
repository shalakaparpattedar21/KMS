import { Outlet } from "react-router-dom";
import TopNavbar from "../../components/navbar/TopNavbar";


export default function MainLayout() {
  return (
    <div className="h-screen flex flex-col">

      <TopNavbar />

      <div className="flex flex-1 overflow-hidden">

       

        <main className="flex-1 bg-slate-100 p-6 overflow-y-auto">
          <Outlet />
        </main>

      </div>

    </div>
  );
}