import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";

export default function AppLayout() {
  return (
    <div className="flex min-h-screen bg-transparent text-slate-900">
      <Sidebar />
      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <Outlet />
      </div>
    </div>
  );
}
