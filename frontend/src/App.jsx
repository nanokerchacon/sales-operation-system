import { useEffect, useState } from "react";
import AppLayout from "./layouts/AppLayout";
import DashboardPage from "./pages/DashboardPage";
import OrderTraceabilityPage from "./pages/OrderTraceabilityPage";

function getCurrentPath() {
  return window.location.pathname;
}

function matchOrderTraceability(pathname) {
  const match = pathname.match(/^\/orders\/(\d+)\/traceability\/?$/);
  if (!match) {
    return null;
  }

  return Number(match[1]);
}

export default function App() {
  const [pathname, setPathname] = useState(getCurrentPath());

  useEffect(() => {
    function handleLocationChange() {
      setPathname(getCurrentPath());
    }

    window.addEventListener("popstate", handleLocationChange);
    return () => {
      window.removeEventListener("popstate", handleLocationChange);
    };
  }, []);

  const orderId = matchOrderTraceability(pathname);

  return (
    <AppLayout>
      {orderId ? <OrderTraceabilityPage orderId={orderId} /> : <DashboardPage />}
    </AppLayout>
  );
}
