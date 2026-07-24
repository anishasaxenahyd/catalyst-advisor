import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { RecommendationProvider } from "./lib/RecommendationContext";
import Landing from "./pages/Landing";
import IdeaInput from "./pages/IdeaInput";
import DesignUpload from "./pages/DesignUpload";
import Analyzing from "./pages/Analyzing";
import { IconSparkles } from "./components/icons";

// The report view pulls in Mermaid (a large, multi-diagram-type library) —
// isolated to its own chunk so Landing/forms/Analyzing never pay for it.
const ReportPage = lazy(() => import("./pages/Report"));

export default function App() {
  return (
    <BrowserRouter>
      <RecommendationProvider>
        <div className="topbar">
          <Link to="/" className="brand" style={{ textDecoration: "none", color: "inherit" }}>
            <IconSparkles width={18} height={18} style={{ color: "var(--accent)" }} />
            <span className="wordmark">Catalyst</span>
          </Link>
          <span className="tagline">AI Solution Advisor — demo, fictional platform</span>
        </div>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/idea" element={<IdeaInput />} />
          <Route path="/design" element={<DesignUpload />} />
          <Route path="/analyzing" element={<Analyzing />} />
          <Route
            path="/report"
            element={
              <Suspense fallback={<main className="page" aria-busy="true" />}>
                <ReportPage />
              </Suspense>
            }
          />
        </Routes>
      </RecommendationProvider>
    </BrowserRouter>
  );
}
