# QMOMS Frontend

React + TypeScript single-page application for the Quarry Mining Operations Monitoring System.

## Tech Stack

- **React** 18.3.0 - UI library with hooks
- **TypeScript** 5.4.0 - Type-safe JavaScript
- **Vite** 6.3.0 - Fast build tool and dev server
- **React Router DOM** 6.23.0 - Client-side routing
- **Axios** 1.7.0 - HTTP client with interceptors
- **MapLibre GL** 4.5.0 - Interactive WebGL maps
- **jsPDF** 2.5.1 + **html2canvas** 1.4.1 - Client-side PDF generation
- **Vitest** 3.1.0 + **fast-check** 3.19.0 - Testing framework with property-based testing

## Project Structure

```
src/
├── pages/              # Top-level page components
│   ├── Dashboard/      # Machine overview
│   ├── MapView/        # Interactive map with real-time positions
│   ├── MachineDetail/  # Single machine view with telemetry
│   ├── TaskPanel/      # Task management
│   ├── Notifications/  # Alerts and conflicts
│   ├── ShiftReport/    # Report generation and viewing
│   ├── Analytics/      # KPI dashboard
│   ├── Zones/          # Zone management
│   ├── Routes/         # Route planning
│   ├── Roles/          # Role & permissions
│   ├── Machinery/      # Machine CRUD
│   └── Login/          # Authentication
├── components/         # Reusable UI components
│   ├── common/         # Shared components (Button, Modal, etc.)
│   ├── layout/         # Layout components (Sidebar, Header)
│   └── [feature]/      # Feature-specific components
├── context/            # React Context providers
│   └── AuthContext.tsx # Authentication state
├── hooks/              # Custom React hooks
│   ├── usePolling.ts   # Auto-refresh data fetching
│   ├── useAuth.ts      # Authentication helpers
│   └── [feature].ts    # Feature-specific hooks
├── types/              # TypeScript type definitions
│   ├── api.ts          # API request/response types
│   └── domain.ts       # Domain model types
├── utils/              # Helper functions
│   ├── api.ts          # Axios instance with auth interceptor
│   └── coordinates.ts  # Map coordinate transformations
├── App.tsx             # Root component with router
├── main.tsx            # React app entry point
└── vite-env.d.ts       # Vite type declarations

tests/                  # Test files
├── property/           # Property-based tests
│   └── coordinates.test.ts
└── components/         # Component tests
```

## Key Features

### Authentication
- JWT-based authentication with automatic token refresh
- Protected routes with role-based access control
- Auth context for global user state
- Axios interceptors for automatic token attachment

### Real-Time Updates
- Custom `usePolling` hook for auto-refresh every 5-10 seconds
- Polls machines, tasks, notifications, telemetry
- Graceful error handling without crashes
- Prevents memory leaks with cleanup on unmount

### Interactive Map
- MapLibre GL for high-performance WebGL rendering
- Custom or Google Maps background images
- Real-time machine position markers
- Antenna reference point markers
- Configurable coordinate calibration
- Click markers to navigate to machine detail

### PDF Report Generation
- Client-side report generation with jsPDF
- Captures DOM elements with html2canvas
- Generates shift reports with metrics, charts, and tables
- Download as PDF without backend rendering

### State Management
- React Context API for global auth state
- Component-level state with hooks
- No Redux/MobX - keeps complexity low for MVP
- Future: Consider Zustand or Jotai if state grows

## Development

### Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit .env with API URL
echo "VITE_API_URL=http://localhost:8000" > .env
```

### Running

```bash
# Start dev server (default: http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Testing

```bash
# Run all tests
npm test

# Run with coverage
npm run test -- --coverage

# Run property-based tests with verbose output
npm test property/
```

## Testing Strategy

The frontend uses a hybrid testing approach:

### Property-Based Testing (fast-check)

Used for pure functions with mathematical properties:
- **Coordinate transformations** - Pixel↔world conversions preserve values
- **Data transformations** - Parsing and serialization round-trips
- **Utility functions** - Pure logic with invariants

Property tests generate hundreds of test cases automatically.

### Component Testing (Vitest + React Testing Library)

Used for:
- UI component behavior
- User interactions (clicks, form submissions)
- Conditional rendering
- Error states

## Key Patterns

### Custom Hooks

```typescript
// usePolling - Auto-refresh data
const { data, error, isLoading } = usePolling<Machine[]>(
  '/machines',
  5000 // interval in ms
);

// useAuth - Authentication helpers
const { user, login, logout, hasRole } = useAuth();
```

### Protected Routes

```typescript
<Route element={<ProtectedRoute allowedRoles={['dispatcher', 'admin']} />}>
  <Route path="/map-config" element={<MapConfigPage />} />
</Route>
```

### API Client

```typescript
// Centralized Axios instance with auth
import { api } from '@/utils/api';

const response = await api.get<Machine[]>('/machines');
const machines = response.data;
```

### Type Safety

All API interactions use TypeScript interfaces matching backend schemas:

```typescript
interface Machine {
  id: string;
  name: string;
  machine_type: string;
  current_state: string;
  pos_x: number | null;
  pos_y: number | null;
  conflict_active: boolean;
  zone_id: string | null;
}
```

## Environment Variables

| Variable | Description | Required | Default |
|---|---|---|---|
| `VITE_API_URL` | Backend API base URL | Yes | - |

Vite exposes env vars prefixed with `VITE_` to the client.

## Styling

- CSS Modules for component-scoped styles
- No UI framework (Material-UI, Ant Design, etc.) for full control
- Custom design system with consistent spacing, colors, typography
- Responsive design for desktop (tablet/mobile TBD)

## MapLibre GL Integration

```typescript
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

useEffect(() => {
  const map = new maplibregl.Map({
    container: mapRef.current,
    style: { /* style object */ },
    center: [lng, lat],
    zoom: 15
  });

  // Add markers
  new maplibregl.Marker()
    .setLngLat([lng, lat])
    .addTo(map);

  return () => map.remove();
}, []);
```

## Coordinate Transformation

Real-world coordinates to pixel coordinates for map overlay:

```typescript
function worldToPixel(
  worldX: number,
  worldY: number,
  bounds: { min_x: number; max_x: number; min_y: number; max_y: number },
  imageWidth: number,
  imageHeight: number
): { px: number; py: number } {
  const px = ((worldX - bounds.min_x) / (bounds.max_x - bounds.min_x)) * imageWidth;
  const py = ((worldY - bounds.min_y) / (bounds.max_y - bounds.min_y)) * imageHeight;
  return { px, py };
}
```

Inverse transformation for click-to-coordinate:

```typescript
function pixelToWorld(
  px: number,
  py: number,
  bounds: { min_x: number; max_x: number; min_y: number; max_y: number },
  imageWidth: number,
  imageHeight: number
): { worldX: number; worldY: number } {
  const worldX = (px / imageWidth) * (bounds.max_x - bounds.min_x) + bounds.min_x;
  const worldY = (py / imageHeight) * (bounds.max_y - bounds.min_y) + bounds.min_y;
  return { worldX, worldY };
}
```

## Polling Strategy

The `usePolling` hook implements smart polling:

```typescript
export function usePolling<T>(endpoint: string, interval: number = 5000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.get<T>(endpoint);
        setData(response.data);
        setError(null);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData(); // Initial fetch
    const intervalId = setInterval(fetchData, interval);

    return () => clearInterval(intervalId); // Cleanup
  }, [endpoint, interval]);

  return { data, error, isLoading };
}
```

- Fetches immediately on mount
- Polls at specified interval
- Cleans up interval on unmount (prevents memory leaks)
- Non-blocking error handling

## Common Issues

### CORS errors
- Verify backend CORS is configured to allow frontend origin
- Check `VITE_API_URL` in `.env` matches backend URL
- Backend should set `Access-Control-Allow-Origin` header

### Authentication issues
- Check JWT token in localStorage: `localStorage.getItem('token')`
- Verify token is included in request headers (check Network tab)
- Token expiry: re-login to get fresh token

### Map not rendering
- Check MapLibre GL CSS is imported
- Verify map container has explicit width/height
- Check browser console for WebGL support warnings

### Polling performance
- Reduce interval if too frequent (5-10 seconds recommended)
- Consider pausing polling when tab is not visible
- Use React DevTools Profiler to identify re-render issues

## Build and Deployment

```bash
# Production build
npm run build

# Output in dist/ directory
ls dist/

# Serve with nginx, Apache, or any static file server
# Example nginx config:
# location / {
#   root /path/to/dist;
#   try_files $uri $uri/ /index.html;
# }
```

### Docker Build

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Adding a New Page

1. Create directory under `src/pages/NewFeature/`
2. Add `index.tsx` with page component
3. Add `NewFeature.module.css` for styles
4. Add route in `src/App.tsx`
5. Add navigation link in `src/components/layout/Sidebar.tsx`
6. Add TypeScript types in `src/types/`
7. Add API client functions if needed
8. Add tests in `tests/pages/NewFeature.test.tsx`

## Performance Optimization

- Use `React.memo()` for expensive components
- Lazy load routes with `React.lazy()` and `Suspense`
- Debounce/throttle frequent events (input, scroll, resize)
- Virtualize long lists with `react-window` if needed
- Use `useMemo` and `useCallback` to prevent unnecessary re-renders
- Profile with React DevTools Profiler

## Accessibility

- Use semantic HTML (`<button>`, `<nav>`, `<main>`, etc.)
- Include `aria-label` on interactive elements
- Ensure keyboard navigation works (Tab, Enter, Escape)
- Test with screen readers (NVDA, JAWS, VoiceOver)
- Maintain color contrast ratios (WCAG AA minimum)
- Provide focus indicators on interactive elements

## Browser Support

- Chrome/Edge 90+ (primary)
- Firefox 88+
- Safari 14+
- WebGL required for map rendering

## Contributing

- Follow existing component structure
- Use TypeScript strict mode
- Add prop types to all components
- Write tests for new features
- Run `npm test` before committing
- Use meaningful commit messages
