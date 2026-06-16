import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 20_000,
});

export const useMocks = (process.env.NEXT_PUBLIC_USE_MOCKS ?? "true") === "true";
