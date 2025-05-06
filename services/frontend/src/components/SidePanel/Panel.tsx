import { useStore } from "../../lib/store";
import NearbyList from "./NearbyList";
import QuickFacts from "./QuickFacts";

export default function Panel() {
  const { reverse, selectedFeature } = useStore();

  return (
    <div className="absolute right-4 top-4 bottom-4 w-80 bg-white rounded-lg shadow-lg p-4 overflow-y-auto">
      {/* Reverse geocoding info */}
      {reverse && (
        <div>
          {reverse.county && (
            <div className="text-sm text-gray-600">
              County: <span className="font-medium">{reverse.county.name}</span>
            </div>
          )}
          {reverse.msa && (
            <div className="text-sm text-gray-600">
              MSA: <span className="font-medium">{reverse.msa.name}</span>
            </div>
          )}
        </div>
      )}

      {/* Nearby places */}
      <NearbyList />

      {/* Region quick facts */}
      {selectedFeature && (
        <div>
          <h3 className="text-lg font-semibold mb-2">
            {selectedFeature.properties.name as string}
          </h3>
          <QuickFacts />
        </div>
      )}
    </div>
  );
}
