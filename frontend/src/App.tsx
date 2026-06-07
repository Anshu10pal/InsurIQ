import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import InvestigationPage from "./pages/InvestigationPage";
import DashboardPage from "./pages/DashboardPage";
import ScoreClaimPage from "./pages/ScoreClaimPage";
import EvalPage from "./pages/EvalPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"            element={<Navigate to="/investigate" replace />} />
        <Route path="/investigate" element={<InvestigationPage />} />
        <Route path="/dashboard"   element={<DashboardPage />} />
        <Route path="/score"       element={<ScoreClaimPage />} />
        <Route path="/eval"        element={<EvalPage />} />
      </Routes>
    </BrowserRouter>
  );
}
