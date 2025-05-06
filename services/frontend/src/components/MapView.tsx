import { useEffect, useRef, useCallback } from "react";
import maplibregl from "maplibre-gl";
import type { StyleSpecification } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useStore } from "../lib/store";
import type { Layer } from "../lib/api";
import InteractionModePicker from "./InteractionModePicker";

const generateStyle = (layer: Layer): StyleSpecification => ({
  version: 8,
  sources: {
    // Your vector tile source
    "vector-tiles": {
      type: "vector",
      tiles: [
        `${import.meta.env.VITE_API_URL}/v1/tiles/${layer}/{z}/{x}/{y}.mvt`,
      ],
      maxzoom: 22,
    },
  },
  layers: [
    // Base background
    {
      id: "background",
      type: "background",
      paint: {
        "background-color": "#f8f9fa",
      },
    },
    // Your vector tile layers
    {
      id: "fill",
      type: "fill",
      source: "vector-tiles",
      "source-layer": "layer",
      paint: {
        "fill-color": "#e9ecef",
        "fill-outline-color": "#dee2e6",
      },
    },
    {
      id: `${layer}-outline`,
      type: "line",
      source: "vector-tiles",
      "source-layer": "layer",
      paint: {
        "line-color": "#ced4da",
        "line-width": 1,
      },
    },
    {
      id: "selected-feature",
      type: "fill",
      source: "vector-tiles",
      "source-layer": "layer",
      paint: {
        "fill-color": "#4dabf7",
        "fill-opacity": 0.5,
      },
      filter: ["==", ["get", "geoid"], ""],
    },
  ],
});

// Cache styles for each layer
const styleCache = new Map<Layer, StyleSpecification>();

const getStyle = (layer: Layer): StyleSpecification => {
  if (!styleCache.has(layer)) {
    styleCache.set(layer, generateStyle(layer));
  }
  return styleCache.get(layer)!;
};

export default function MapView() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const marker = useRef<maplibregl.Marker | null>(null);
  const {
    activeLayer,
    interactionMode,
    pin,
    setPin,
    selectedFeature,
    setSelectedFeature,
  } = useStore();

  // Move click handler to useCallback
  const handleMapClick = useCallback(
    (e: maplibregl.MapMouseEvent) => {
      const mapInstance = map.current;
      if (!mapInstance || !mapInstance.loaded()) return;

      const { lng: lon, lat } = e.lngLat;

      if (interactionMode === "select") {
        // Check if clicked on a feature
        const features = mapInstance.queryRenderedFeatures(e.point, {
          layers: ["fill"],
        });

        if (features.length > 0) {
          const feature = features[0];
          setSelectedFeature({
            id: feature.properties?.geoid,
            layer: activeLayer,
            properties: feature.properties,
          });
        }
      } else if (interactionMode === "marker") {
        setPin({ lat, lon });
      }
    },
    [interactionMode, setSelectedFeature, setPin, activeLayer]
  );

  // Highlight the feature when it is selected
  useEffect(() => {
    const mapInstance = map.current;
    if (!mapInstance || !mapInstance.loaded()) return;

    // Update the filter on the highlight layer
    mapInstance.setFilter("selected-feature", [
      "==",
      ["get", "geoid"],
      selectedFeature?.id ?? "",
    ]);
  }, [selectedFeature]);

  // Initialize map only once when component mounts
  useEffect(() => {
    if (!mapContainer.current) return;

    try {
      const initialStyle = getStyle(activeLayer);

      map.current = new maplibregl.Map({
        container: mapContainer.current,
        style: initialStyle,
        center: [-98.5795, 39.8283],
        zoom: 3,
      });

      const mapInstance = map.current;

      // Add debug listeners
      mapInstance.on("error", (e) => {
        // TODO: Observability : Log to Sentry
        console.error("MapLibre error:", e);
      });

      return () => {
        if (marker.current) {
          marker.current.remove();
        }
        mapInstance.remove();
      };
    } catch (error) {
      console.error("Error initializing map:", error);
    }
  }, []); // Empty dependency array since we only want to initialize once

  // Update style when activeLayer changes
  useEffect(() => {
    const mapInstance = map.current;
    if (!mapInstance || !mapInstance.loaded()) return;

    const newStyle = getStyle(activeLayer);
    mapInstance.setStyle(newStyle);
  }, [activeLayer]);

  // Reset selected feature when active layer changes
  useEffect(() => {
    setSelectedFeature(null);
  }, [activeLayer, setSelectedFeature]);

  // Update selected feature highlighting when selection changes
  useEffect(() => {
    const mapInstance = map.current;
    if (!mapInstance || !mapInstance.loaded()) return;

    mapInstance.setFilter(
      "selected-feature",
      selectedFeature
        ? ["==", ["get", "geoid"], selectedFeature.id]
        : ["==", ["get", "geoid"], ""]
    );
  }, [selectedFeature]);

  // Update click handler effect to use the memoized function
  useEffect(() => {
    const mapInstance = map.current;
    if (!mapInstance) return;

    mapInstance.on("click", handleMapClick);

    return () => {
      mapInstance.off("click", handleMapClick);
    };
  }, [handleMapClick, map]);

  useEffect(() => {
    const mapInstance = map.current;
    if (!mapInstance) return;

    // Remove existing marker if any
    if (marker.current) {
      marker.current.remove();
    }

    if (!pin) return;

    // Create new marker
    marker.current = new maplibregl.Marker()
      .setLngLat([pin.lon, pin.lat])
      .addTo(mapInstance);
  }, [pin]);

  return (
    <>
      <InteractionModePicker />
      <div
        ref={mapContainer}
        className="w-full h-full"
        style={{ position: "absolute", top: 0, bottom: 0, left: 0, right: 0 }}
      />
    </>
  );
}
