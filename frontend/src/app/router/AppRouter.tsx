import { BrowserRouter, Routes, Route } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import Login from "../../pages/Login";
import Dashboard from "../../pages/Dashboard";
import Search from "../../pages/Search";
import Documents from "../../pages/Documents";
import Users from "../../pages/Users";
import Settings from "../../pages/Settings";
import DocumentPreview from "../../pages/DocumentPreview";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
<Route path="/" element={<Login />} />

<Route element={<MainLayout />}>
  <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/search" element={<Search />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/documents/:id" element={<DocumentPreview />} />
          <Route path="/users" element={<Users />} />
          <Route path="/settings" element={<Settings />} />
        </Route>

      </Routes>
    </BrowserRouter>
  );
}