import { create } from "zustand";
import type { Layer, NearbyPlace, ReverseResponse } from "./api";
import { getNearby, getReverse, getQuickFacts } from "./api";

type InteractionMode = "select" | "marker";

interface AppState {
  activeLayer: Layer;
  interactionMode: InteractionMode;
  pin: { lat: number; lon: number } | null;
  nearby: NearbyPlace[] | null;
  reverse: ReverseResponse | null;
  quickfacts: Record<string, unknown> | null;
  selectedFeature: { id: string; properties: Record<string, unknown> } | null;

  // Actions
  setLayer: (layer: Layer) => void;
  setInteractionMode: (mode: InteractionMode) => void;
  setPin: (pin: { lat: number; lon: number } | null) => Promise<void>;
  setSelectedFeature: (
    feature: {
      id: string;
      layer: Layer;
      properties: Record<string, unknown>;
    } | null
  ) => void;
}

export const useStore = create<AppState>((set) => ({
  // Initial state
  activeLayer: "states",
  interactionMode: "marker",
  pin: null,
  nearby: null,
  reverse: null,
  quickfacts: null,
  selectedFeature: null,

  // Actions
  setLayer: (layer) => set({ activeLayer: layer }),
  setInteractionMode: (mode) => {
    set({ interactionMode: mode });
  },
  setSelectedFeature: async (feature) => {
    set({ selectedFeature: feature });
    if (!feature) {
      set({ quickfacts: null });
      return;
    }

    if (feature.layer !== "msas") {
      try {
        const quickfacts = await getQuickFacts(feature.layer, feature.id);
        set({ quickfacts });
      } catch (error) {
        console.error("Error fetching quickfacts:", error);
        set({ quickfacts: null });
      }
    }
  },
  setPin: async (pin: { lat: number; lon: number } | null) => {
    set({ pin });
    if (!pin) {
      set({ nearby: null, reverse: null });
      return;
    }

    try {
      const [nearby, reverse] = await Promise.all([
        getNearby(pin.lat, pin.lon),
        getReverse(pin.lat, pin.lon),
      ]);
      set({ nearby, reverse });
    } catch (error) {
      console.error("Error fetching pin data:", error);
      set({ nearby: null, reverse: null });
    }
  },
}));
