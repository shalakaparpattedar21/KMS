import AppHeader from "../../components/header/AppHeader";

export default function Settings() {
  return (
    <>
      <AppHeader />

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-5 shadow">
          <h2 className="font-bold mb-3">
            Profile
          </h2>

          <p>Name: Shalaka</p>
          <p>Email: shalaka@company.com</p>
        </div>

        <div className="bg-white rounded-xl p-5 shadow">
          <h2 className="font-bold mb-3">
            Google Drive
          </h2>

          <p>Status: Connected</p>
        </div>
      </div>
    </>
  );
}