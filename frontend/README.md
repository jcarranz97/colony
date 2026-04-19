# Colony Frontend

Next.js 16 frontend for the Colony expense management app.

## Getting Started

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Running with Docker

```bash
docker-compose up --build
```

## Environment Variables

| Variable              | Description                 |
| --------------------- | --------------------------- |
| `NEXT_PUBLIC_API_URL` | Colony backend API base URL |

Copy `.env.example` to `.env.local` and fill in the values.
