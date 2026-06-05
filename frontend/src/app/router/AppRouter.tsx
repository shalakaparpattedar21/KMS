import { BrowserRouter, Routes, Route } from "react-router-dom";

import Users from "../../pages/Users";
import Login from "../../pages/Login";
import MainLayout from "../layouts/MainLayout";

import Dashboard from "../../pages/Dashboard";
import Search from "../../pages/Search";
import Documents from "../../pages/Documents";
import Activity from "../../pages/Activity";
import Settings from "../../pages/Settings";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
<Route path="/" element={<Login />} />

<Route element={<MainLayout />}>
  <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/search" element={<Search />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/users" element={<Users />} />
          <Route path="/activity" element={<Activity />} />
          <Route path="/settings" element={<Settings />} />
        </Route>

      </Routes>
    </BrowserRouter>
  );
}