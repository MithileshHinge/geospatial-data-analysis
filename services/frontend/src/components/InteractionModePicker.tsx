import { useEffect } from "react";
import { useStore } from "../lib/store";

const modes = [
  { id: "select" as const, label: "Select Mode" },
  { id: "marker" as const, label: "Place Marker" },
];

export default function InteractionModePicker() {
  const { interactionMode, setInteractionMode, setSelectedFeature, setPin } =
    useStore();

  // Reset the selected feature and pin when the interaction mode changes
  useEffect(() => {
    if (interactionMode === "marker") {
      setSelectedFeature(null);
    } else if (interactionMode === "select") {
      setPin(null);
    }
  }, [interactionMode, setSelectedFeature, setPin]);

  return (
    <div className="absolute top-20 left-4 bg-white rounded-lg shadow-lg p-2 z-10">
      <div className="flex gap-2">
        {modes.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => {
              setInteractionMode(id);
            }}
            className={`
              px-4 py-2 rounded-md transition-colors
              ${
                interactionMode === id
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
