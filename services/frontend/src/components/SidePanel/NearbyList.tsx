import { useStore } from "../../lib/store";

export default function NearbyList() {
  const { nearby } = useStore();

  if (!nearby) return null;

  return (
    <div className="mt-4">
      <h3 className="text-lg font-semibold mb-2">Nearby Places</h3>
      <div className="space-y-2">
        {nearby.map((place) => (
          <div key={place.geoid} className="bg-gray-50 p-3 rounded-md">
            <div className="font-medium">{place.name}</div>
            <div className="text-sm text-gray-500">
              {place.distance_km.toFixed(1)} km away
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
