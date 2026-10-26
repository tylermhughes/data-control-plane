import { Navigate, Route, Routes } from "react-router";

import { Layout } from "./components/Layout";
import { BatchPage } from "./pages/Batch";
import { Board } from "./pages/Board";
import { Lineage } from "./pages/Lineage";
import { Portfolio } from "./pages/Portfolio";
import { RequestPage } from "./pages/Request";
import { Requests } from "./pages/Requests";
import { Settings } from "./pages/Settings";
import { SourcePage } from "./pages/Source";
import { Sources } from "./pages/Sources";
import { Specs } from "./pages/Specs";
import { SignIn } from "./pages/SignIn";
import { useSession } from "./session";
import { TutorialProvider } from "./tutorial/engine";
import { STEPS } from "./tutorial/steps";

export function App() {
  const { key } = useSession();
  if (!key) return <SignIn />;
  return (
    <TutorialProvider steps={STEPS}>
      <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/portfolio" replace />} />
        <Route path="portfolio" element={<Portfolio />} />
        <Route path="board" element={<Board />} />
        <Route path="batches/:batchId" element={<BatchPage />} />
        <Route path="specs" element={<Specs />} />
        <Route path="specs/:specId" element={<Specs />} />
        <Route path="requests" element={<Requests />} />
        <Route path="requests/:requestId" element={<RequestPage />} />
        <Route path="sources" element={<Sources />} />
        <Route path="sources/:sourceId" element={<SourcePage />} />
        <Route path="lineage" element={<Lineage />} />
        <Route path="lineage/:datasetId" element={<Lineage />} />
        <Route path="settings" element={<Settings />} />
        <Route path="settings/:tab" element={<Settings />} />
        <Route path="*" element={<Navigate to="/portfolio" replace />} />
      </Route>
      </Routes>
    </TutorialProvider>
  );
}
