# WorkersBridge Web

React + Vite web client for the existing Django REST backend.

## UI Direction

Approved UI reference images are saved in:

```text
src/assets/ui-references/
```

The app theme uses warm white surfaces, deep charcoal text, emerald/teal primary actions, and amber accents for ratings and earnings.

## Run

```bash
npm install
npm run dev
```

Set `VITE_API_BASE_URL` in `.env` if Django is not running at `http://127.0.0.1:8000`.
