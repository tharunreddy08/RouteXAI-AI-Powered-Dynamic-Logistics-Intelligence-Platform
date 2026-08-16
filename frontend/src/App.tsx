import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider, RequireAuth } from "./lib/auth";
import { ToastProvider } from "./lib/toast";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import OrdersPage from "./pages/OrdersPage";
import ManualOrderEntryPage from "./pages/ManualOrderEntryPage";
import FleetMapPage from "./pages/FleetMapPage";
import HardwareDemoPage from "./pages/HardwareDemoPage";
import RiderPerformancePage from "./pages/RiderPerformancePage";
import RouteHistoryPage from "./pages/RouteHistoryPage";
import AnalyticsPage from "./pages/AnalyticsPage";

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            <Route
              element={
                <RequireAuth>
                  <Layout />
                </RequireAuth>
              }
            >
              <Route path="/" element={<DashboardPage />} />
              <Route
                path="/orders"
                element={
                  <RequireAuth roles={["admin", "dispatcher"]}>
                    <OrdersPage />
                  </RequireAuth>
                }
              />
              <Route
                path="/orders/new"
                element={
                  <RequireAuth roles={["admin", "dispatcher"]}>
                    <ManualOrderEntryPage />
                  </RequireAuth>
                }
              />
              <Route path="/fleet" element={<FleetMapPage />} />
              <Route
                path="/hardware"
                element={
                  <RequireAuth roles={["admin", "dispatcher"]}>
                    <HardwareDemoPage />
                  </RequireAuth>
                }
              />
              <Route
                path="/riders"
                element={
                  <RequireAuth roles={["admin", "dispatcher"]}>
                    <RiderPerformancePage />
                  </RequireAuth>
                }
              />
              <Route path="/route-history" element={<RouteHistoryPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
            </Route>
          </Routes>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}
