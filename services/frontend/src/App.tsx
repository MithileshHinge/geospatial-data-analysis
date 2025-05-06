import { useState } from "react";
import MapView from "./components/MapView";
import LayerPicker from "./components/LayerPicker";
import Panel from "./components/SidePanel/Panel";
import ErrorToast from "./components/ErrorToast";
import "./App.css";

export default function App() {
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="w-screen h-screen relative">
      <MapView />
      <LayerPicker />
      <Panel />
      {error && <ErrorToast message={error} onClose={() => setError(null)} />}
    </div>
  );
}
