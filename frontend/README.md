# Multimodal Product Catalogue Intelligence

AI-powered product discovery frontend built with **Next.js 15 (App Router)**, **TypeScript**, **TailwindCSS**, **Shadcn UI**, **Framer Motion**, **TanStack Query**, and **Axios**.

## Quick start

```bash
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000.

## Env

- `NEXT_PUBLIC_API_URL` — base URL of the backend
- `NEXT_PUBLIC_USE_MOCKS` — `true` to use bundled mock data, `false` to hit the real API

## Endpoints expected

- `POST /search/text` `{ query }`
- `POST /search/image` multipart `image`
- `POST /search/multimodal` multipart `image`, `query`
- `GET /products/{id}`
- `GET /analytics`

## Structure

```
src/
  app/                  # Routes (App Router)
  components/           # Reusable UI + feature components
  hooks/                # React Query hooks
  services/             # Axios API layer
  types/                # Shared TS types
  mocks/                # Mock data
  lib/                  # Utilities + query client
```
