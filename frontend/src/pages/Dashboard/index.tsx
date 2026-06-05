import AppHeader from "../../components/header/AppHeader";
import StatsCard from "../../components/dashboard/StatsCard";

export default function Dashboard() {
  return (
    <>
      <AppHeader />

      <div>
        <h1 className="text-3xl font-bold mb-6">
          Dashboard
        </h1>

        <div className="grid grid-cols-4 gap-4">
          <StatsCard title="Connected Users" value="128" />
          <StatsCard title="Documents" value="1245" />
          <StatsCard title="Searches Today" value="348" />
          <StatsCard title="Connected Drives" value="96" />
        </div>
      </div>
    </>
  );
}