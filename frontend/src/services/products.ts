import { api, useMocks } from "./api";
import { mockProducts, mockAnalytics } from "@/mocks/data";
import type { Product, SearchResponse, AnalyticsData } from "@/types";

const delay = <T,>(v: T, ms = 600) => new Promise<T>((r) => setTimeout(() => r(v), ms));

function filterByQuery(q: string): Product[] {
  const s = q.toLowerCase().trim();
  if (!s) return mockProducts;
  return mockProducts
    .map((p) => ({
      ...p,
      score:
        (p.name.toLowerCase().includes(s) ? 0.4 : 0) +
        (p.description.toLowerCase().includes(s) ? 0.3 : 0) +
        (p.category.toLowerCase().includes(s) ? 0.2 : 0) +
        Math.random() * 0.2,
    }))
    .filter((p) => (p.score ?? 0) > 0.2)
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
}

export async function searchText(query: string): Promise<SearchResponse> {
  if (useMocks) return delay({ results: filterByQuery(query) });
  const { data } = await api.post<SearchResponse>("/search/text", { query });
  return data;
}

export async function searchImage(image: File): Promise<SearchResponse> {
  if (useMocks) return delay({ results: [...mockProducts].sort(() => Math.random() - 0.5).slice(0, 6) });
  const form = new FormData();
  form.append("image", image);
  const { data } = await api.post<SearchResponse>("/search/image", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function searchMultimodal(image: File, query: string): Promise<SearchResponse> {
  if (useMocks) {
    const results = filterByQuery(query).slice(0, 6);
    return delay({ results: results.length ? results : mockProducts.slice(0, 4) });
  }
  const form = new FormData();
  form.append("image", image);
  form.append("query", query);
  const { data } = await api.post<SearchResponse>("/search/multimodal", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getProduct(id: number | string): Promise<Product> {
  if (useMocks) {
    const found = mockProducts.find((p) => String(p.id) === String(id));
    if (!found) throw new Error("Product not found");
    return delay(found, 300);
  }
  const { data } = await api.get<Product>(`/products/${id}`);
  return data;
}

export async function getAnalytics(): Promise<AnalyticsData> {
  if (useMocks) return delay(mockAnalytics, 400);
  const { data } = await api.get<AnalyticsData>("/analytics");
  return data;
}
