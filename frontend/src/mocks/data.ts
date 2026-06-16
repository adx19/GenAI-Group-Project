import type { Product, AnalyticsData } from "@/types";

const img = (seed: string) =>
  `https://images.unsplash.com/photo-${seed}?auto=format&fit=crop&w=800&q=80`;

export const mockProducts: Product[] = [
  {
    id: 1,
    name: "Ergonomic Black Office Chair",
    description: "High-back mesh chair with adjustable lumbar support and 4D armrests for all-day comfort.",
    image_url: img("1505843490701-5be5b1b31f8f"),
    category: "Chair",
    score: 0.94,
    attributes: { color: "Black", material: "Mesh", style: "Modern", shape: "High Back" },
  },
  {
    id: 2,
    name: "Walnut Mid-Century Lounge",
    description: "Solid walnut frame with curved backrest and premium leather cushioning.",
    image_url: img("1567538096630-e0c55bd6374c"),
    category: "Chair",
    score: 0.89,
    attributes: { color: "Brown", material: "Wood", style: "Mid-Century", shape: "Curved Back" },
  },
  {
    id: 3,
    name: "Scandinavian Linen Sofa",
    description: "Minimalist 3-seater with oak legs and stain-resistant linen upholstery.",
    image_url: img("1555041469-a586c61ea9bc"),
    category: "Sofa",
    score: 0.86,
    attributes: { color: "Beige", material: "Linen", style: "Scandinavian", shape: "Straight" },
  },
  {
    id: 4,
    name: "Industrial Oak Desk",
    description: "Reclaimed oak top on powder-coated steel frame. Cable management included.",
    image_url: img("1518455027359-f3f8164ba6bd"),
    category: "Desk",
    score: 0.82,
    attributes: { color: "Oak", material: "Wood + Steel", style: "Industrial", shape: "Rectangular" },
  },
  {
    id: 5,
    name: "Matte Ceramic Pendant Lamp",
    description: "Hand-finished ceramic shade with warm dimmable LED.",
    image_url: img("1513506003901-1e6a229e2d15"),
    category: "Lighting",
    score: 0.78,
    attributes: { color: "White", material: "Ceramic", style: "Modern", shape: "Dome" },
  },
  {
    id: 6,
    name: "Velvet Accent Armchair",
    description: "Plush emerald velvet with brass tapered legs.",
    image_url: img("1506439773649-6e0eb8cfb237"),
    category: "Chair",
    score: 0.75,
    attributes: { color: "Green", material: "Velvet", style: "Glam", shape: "Tub" },
  },
  {
    id: 7,
    name: "Round Marble Coffee Table",
    description: "Carrara marble top with sculptural matte black base.",
    image_url: img("1493663284031-b7e3aefcae8e"),
    category: "Table",
    score: 0.72,
    attributes: { color: "White", material: "Marble", style: "Contemporary", shape: "Round" },
  },
  {
    id: 8,
    name: "Woven Rattan Bookshelf",
    description: "Open shelving with natural rattan paneling and solid teak frame.",
    image_url: img("1493663284031-b7e3aefcae8e"),
    category: "Storage",
    score: 0.70,
    attributes: { color: "Natural", material: "Rattan", style: "Bohemian", shape: "Tall" },
  },
];

export const mockAnalytics: AnalyticsData = {
  total_searches: 1250,
  text_searches: 600,
  image_searches: 350,
  multimodal_searches: 300,
  ctr: 0.67,
  abandonment_rate: 0.12,
  zero_result_searches: 40,
};
