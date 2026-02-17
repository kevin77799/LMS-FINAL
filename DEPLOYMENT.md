# Deployment Guide: Vercel + Hugging Face (NO CARD REQUIRED)

This guide explains how to deploy your LMS application for free without a credit card. We use **Hugging Face Spaces** for the backend and **Vercel** for the frontend.

## 1. Backend Deployment (Hugging Face)

Hugging Face Spaces provides free hosting for Docker/Python apps and does not require a credit card.

### Steps:
1.  **Commit and Push your code to GitHub.**
2.  Log in to [Hugging Face](https://huggingface.co/).
3.  Click **New** > **Space**.
4.  **Settings:**
    *   **Space Name**: `lms-backend` (or your choice)
    *   **SDK**: `Docker` (**IMPORTANT**: Select "Blank" or "Docker" - we will use a Dockerfile for the best control).
    *   **Public/Private**: Public (so Vercel can talk to it).
5.  Once the space is created, go to **Settings** > **Variables and Secrets**.
6.  Add a **Secret**:
    *   **Key**: `GOOGLE_API_KEY_1`
    *   **Value**: Your actual Gemini API key.
7.  Upload the files (or connect your GitHub repo if you have a Pro account). Hugging Face will automatically use the `Dockerfile` at the root of the project to build the app.

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
    *   **Value**: Your Hugging Face Space URL (e.g., `https://kevin-lms-backend.hf.space`)
6.  Click **Deploy**.

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
