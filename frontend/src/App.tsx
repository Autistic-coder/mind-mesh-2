import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./auth";
import { AppShell, Status } from "./components";
import { AccountPage } from "./pages/AccountPage";
import { AskPage } from "./pages/AskPage";
import { AuthPage } from "./pages/AuthPage";
import { BatchPage } from "./pages/BatchPage";
import { HistoryPage } from "./pages/HistoryPage";
import { ModelReportPage } from "./pages/ModelReportPage";
import { OverviewPage } from "./pages/OverviewPage";
import { PredictionPage } from "./pages/PredictionPage";

function Protected() {
  const { user, loading } = useAuth(); const location = useLocation();
  if (loading) return <main className="flex min-h-screen items-center justify-center bg-ivory"><Status>Restoring your secure session…</Status></main>;
  return user ? <Outlet /> : <Navigate to="/login" replace state={{ from: location.pathname }} />;
}
export default function App() {
  return <Routes><Route path="/login" element={<AuthPage mode="login" />} /><Route path="/register" element={<AuthPage mode="register" />} /><Route element={<Protected />}><Route element={<AppShell />}><Route index element={<OverviewPage />} /><Route path="prediction" element={<PredictionPage />} /><Route path="batch" element={<BatchPage />} /><Route path="history" element={<HistoryPage />} /><Route path="model" element={<ModelReportPage />} /><Route path="ask" element={<AskPage />} /><Route path="account" element={<AccountPage />} /></Route></Route><Route path="*" element={<Navigate to="/" replace />} /></Routes>;
}

