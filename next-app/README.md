# Next.js Frontend for MVPFOREX

This is the Next.js 14 frontend for your MVPFOREX project. It serves as the main UI and fetches data from your Flask backend at `/api/`.

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```
2. Copy `.env.local.example` to `.env.local` and set your environment variables:
   - `NEXT_PUBLIC_API_URL` (Flask backend URL)
   - `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. Start the development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Testing

This project uses Playwright for end-to-end, integration, and performance testing.

- Run all tests (across Chromium, Firefox, Safari):
  ```bash
  npx playwright test
  ```
- View HTML test report:
  ```bash
  npx playwright show-report
  ```

## Deployment

You can deploy this app to Vercel, Netlify, or any Node.js host.

- For Vercel: push the repo and connect via the Vercel dashboard.
- For Netlify: use `netlify.toml` (if present) or configure build as `npm run build` and publish `.next`.
- Ensure production environment variables are set in your deploy dashboard.

## API Endpoints

- `/api/market-data` – Proxies market data from Flask backend (with fallback)
- `/api/feedback` – Handles user feedback (stored in Supabase)
- `/api/health` – Health check endpoint

## Security & Monitoring

- **Never commit secrets**: Use `.env.local` for local dev, dashboard for production.
- Backend and frontend log errors to console. For advanced monitoring, integrate Sentry or LogRocket.

## Project Structure

```
/next-app
  /components    # React UI components
  /pages         # Next.js pages and API routes
  /tests         # Playwright tests (integration, supabase, performance)
  /utils         # Supabase and helper utilities
  next.config.js # Next.js config (API proxy, CORS)
```

For backend and fullstack details, see the main project README.
