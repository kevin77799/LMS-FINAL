# Deployment Guide: Vercel + Render

This guide explains how to deploy your LMS application with a **Vercel** frontend and a **Render** backend using **SQLite** with persistent storage.

## 1. Backend Deployment (Render)

Render will host your FastAPI server and your SQLite database.

### Steps:
1.  **Push your code to GitHub.**
2.  Log in to [Render.com](https://render.com).
3.  Click **New +** > **Blueprint**.
4.  Connect your GitHub repository.
5.  Render will automatically detect the `render.yaml` file and set up:
    *   A Web Service for the FastAPI app.
    *   A **Persistent Disk** (1GB) mounted at `/data` to store your SQLite database.
6.  Go to the **Environment** tab of your new service and ensure `GOOGLE_API_KEY_1` is set with your actual Gemini API key.
7.  Copy your backend URL (e.g., `https://lms-backend.onrender.com`).

> [!IMPORTANT]
> The database is stored on a persistent disk. This means your data will **not** be deleted when the server restarts or when you deploy new code.

---

## 2. Frontend Deployment (Vercel)

Vercel will host your React application.

### Steps:
1.  Log in to [Vercel.com](https://vercel.com).
2.  Click **Add New** > **Project**.
3.  Import your GitHub repository.
4.  In the **Build & Development Settings**:
    *   **Framework Preset**: Vite
    *   **Root Directory**: `frontend`
5.  In the **Environment Variables** section, add:
    *   **Key**: `VITE_API_URL`
    *   **Value**: Your Render Backend URL (e.g., `https://lms-backend.onrender.com`)
6.  Click **Deploy**.

---

## 3. Environment Variables Summary

### Backend (Render)
| Variable | Value |
| :--- | :--- |
| `GOOGLE_API_KEY_1` | Your Gemini API Key |
| `DB_PATH` | `/data/student_analyzer.db` (Set automatically by Blueprint) |

### Frontend (Vercel)
| Variable | Value |
| :--- | :--- |
| `VITE_API_URL` | Your Backend URL (e.g., `https://your-app.onrender.com`) |

---

## 4. Local Development vs. Production

*   **Local**: The app uses the proxy in `vite.config.ts` (sending requests to `/api`).
*   **Production**: The app uses the `VITE_API_URL` variable to talk directly to Render.
