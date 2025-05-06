# Geo Data Visualization Frontend

A React-based web client for visualizing geographic data using MapLibre GL JS.

## Features

- Interactive map with vector tile layers (States, Counties, MSAs)
- Drop-pin functionality to find nearby towns
- Reverse geocoding to identify regions
- Region highlighting with Census QuickFacts display
- Offline-safe with graceful error handling

## Tech Stack

- React 18 + Vite
- MapLibre GL JS
- Zustand for state management
- Tailwind CSS for styling
- TypeScript for type safety
- Vitest + React Testing Library for testing

## Getting Started

1. Install dependencies:

   ```bash
   pnpm install
   ```

2. Set up environment variables:
   Create a `.env.local` file:

   ```
   VITE_API_URL=http://localhost:8000
   ```

3. Start development server:

   ```bash
   pnpm dev
   ```

4. Run tests:

   ```bash
   pnpm test
   ```

5. Build for production:
   ```bash
   pnpm build
   ```

## Docker

Build and run with Docker:

```bash
docker build -t geo-data-viz-frontend .
docker run -p 8080:80 geo-data-viz-frontend
```

Or use docker-compose:

```bash
docker compose up frontend
```

## Development Notes

- Map tiles are served from `/v1/tiles/{layer}/{z}/{x}/{y}.mvt`
- API endpoints are documented in the API contract
