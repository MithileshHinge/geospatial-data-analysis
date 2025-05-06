import axios from "axios";

// Types based on API contract
export type Layer = "states" | "counties" | "msas" | "places";
export type Format = "mvt" | "geojson";

export interface NearbyPlace {
  geoid: string;
  name: string;
  lat: number;
  lon: number;
  distance_km: number;
}

export interface ReverseResponse {
  county?: { geoid: string; name: string };
  msa?: { geoid: string; name: string };
}

// QuickFacts response type
export interface QuickFactsResponse {
  [key: string]: string | number | boolean | null;
}

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

// Add interceptor for tile requests
api.interceptors.request.use((config) => {
  if (config.url?.includes("/tiles/")) {
    const cacheBust = Date.now();
    config.url += `?cachebust=${cacheBust}`;
  }
  return config;
});

// API helper functions
export const getTileUrl = (
  layer: Layer,
  z: number,
  x: number,
  y: number,
  format: Format = "mvt"
) => {
  const url = `${
    import.meta.env.VITE_API_URL
  }/v1/tiles/${layer}/${z}/${x}/${y}.${format}`;
  console.log("Generated tile URL:", url);
  return url;
};

export const getNearby = async (
  lat: number,
  lon: number,
  radius_km: number = 50,
  limit: number = 25
) => {
  const response = await api.get<{ results: NearbyPlace[] }>(
    "/v1/places/nearby",
    {
      params: { lat, lon, radius_km, limit },
    }
  );
  return response.data.results;
};

export const getReverse = async (
  lat: number,
  lon: number,
  layers: ("counties" | "msas")[] = ["counties", "msas"]
) => {
  const response = await api.get<ReverseResponse>("/v1/reverse", {
    params: { lat, lon, layers: layers.join(",") },
  });
  return response.data;
};

export const getQuickFacts = async (layer: Layer, geoid: string) => {
  const response = await api.get<QuickFactsResponse>(
    `/v1/quickfacts/${layer}/${geoid}`
  );
  return response.data;
};

export default api;
