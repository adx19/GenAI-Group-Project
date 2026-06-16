export interface ProductAttributes {
  color?: string;
  material?: string;
  style?: string;
  shape?: string;
  [key: string]: string | undefined;
}

export interface Product {
  id: number;
  name: string;
  description: string;
  image_url: string;
  category: string;
  score?: number;
  attributes?: ProductAttributes;
}

export interface SearchResponse {
  results: Product[];
}

export interface AnalyticsData {
  total_searches: number;
  text_searches: number;
  image_searches: number;
  multimodal_searches: number;
  ctr: number;
  abandonment_rate: number;
  zero_result_searches: number;
}
