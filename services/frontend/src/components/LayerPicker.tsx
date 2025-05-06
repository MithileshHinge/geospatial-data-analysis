import { useStore } from "../lib/store";
import type { Layer } from "../lib/api";

const layers: { id: Layer; label: string }[] = [
  { id: "states", label: "States" },
  { id: "counties", label: "Counties" },
  { id: "msas", label: "MSAs" },
  { id: "places", label: "Places" },
];

export default function LayerPicker() {
  const { activeLayer, setLayer } = useStore();

  return (
    <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-2 z-10">
      <div className="flex gap-2">
        {layers.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setLayer(id)}
            className={`
              px-4 py-2 rounded-md transition-colors
              ${
                activeLayer === id
                  ? "bg-blue-500 text-white"
                  : "bg-gray-100 hover:bg-gray-200 text-gray-700"
              }
            `}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
