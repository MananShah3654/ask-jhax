import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import CoPilot from "@/pages/CoPilot";
import { Toaster } from "@/components/ui/sonner";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<CoPilot />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-center" richColors />
    </div>
  );
}

export default App;
