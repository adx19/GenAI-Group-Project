# GenAI Product Discovery System

## Overview

GenAI Product Discovery System is a multimodal product search platform that allows users to discover products using text, images, or a combination of both.

The system uses AI-powered embeddings and similarity search to retrieve relevant products and provides analytics to track user search behavior.

---

## Features

### Text Search

Search products using natural language queries.

### Image Search

Upload an image and retrieve visually similar products.

### Multimodal Search

Combine text and image inputs to improve search relevance.

### Product Details

View product information including:

* Product Name
* Category
* Description
* Extracted Attributes

### Analytics Dashboard

Track:

* Total Searches
* Text Searches
* Image Searches
* Multimodal Searches
* Click Through Rate (CTR)
* Abandonment Rate
* Zero Result Searches

---

## Tech Stack

### Backend

* FastAPI
* PostgreSQL
* SQLAlchemy
* Gemini API
* Sentence Transformers
* FAISS

### Frontend

* Next.js
* TypeScript
* Tailwind CSS
* React Query
* Axios

---

## Project Structure

```text
backend/
frontend/
```

* `backend/` contains APIs, database models, AI services, and search logic.
* `frontend/` contains the Next.js user interface.

---

## Installation

### Backend

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
DATABASE_URL=your_database_url
GEMINI_API_KEY=your_gemini_api_key
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend URL:

```text
http://localhost:8000
```

---

### Frontend

Install dependencies:

```bash
npm install
```

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCKS=false
```

Start the frontend:

```bash
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

---

## Running the Application

1. Start PostgreSQL.
2. Start the FastAPI backend.
3. Start the Next.js frontend.
4. Open `http://localhost:3000`.

---

## Deployment

* Frontend can be deployed using Vercel.
* Backend can be deployed using Render, Railway, or any server supporting FastAPI.
* PostgreSQL is required for persistent storage.

---

## Team Members

* Member 1
* Member 2
* Member 3
* Member 4
* Member 5

---

## Project Demonstration

The system supports:

* Text-based product search
* Image-based product search
* Multimodal product search
* Product analytics dashboard
* Product attribute visualization

---

## Notes

The original raw dataset is not included in the repository due to repository size limitations. All preprocessing, ingestion, embedding generation, and indexing scripts are included in the project.
