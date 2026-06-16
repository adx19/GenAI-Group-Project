"use client";
import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Image as ImageIcon, Type, Wand2 } from "lucide-react";
import { SearchBar } from "@/components/SearchBar";
import { ImageUploader } from "@/components/ImageUploader";
import { MultimodalSearchForm } from "@/components/MultimodalSearchForm";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ProductGrid } from "@/components/ProductGrid";
import { ProductGridSkeleton } from "@/components/LoadingSkeleton";
import { ErrorState } from "@/components/ErrorState";
import { EmptyState } from "@/components/EmptyState";
import { Sidebar } from "@/components/Sidebar";
import { useImageSearch, useMultimodalSearch, useTextSearch } from "@/hooks/use-search";
import type { Product } from "@/types";

export default function HomePage() {
  const text = useTextSearch();
  const image = useImageSearch();
  const multi = useMultimodalSearch();
  const [imgFile, setImgFile] = useState<File | null>(null);
  const [filters, setFilters] = useState<Record<string, string | null>>({});

  const activeMutation = [text, image, multi].find((m) => m.isPending) ?? null;
  const error = text.error || image.error || multi.error;
  const results: Product[] =
    multi.data?.results ?? image.data?.results ?? text.data?.results ?? [];

  const filtered = useMemo(() => {
    return results.filter((p) =>
      Object.entries(filters).every(([k, v]) => {
        if (!v) return true;
        if (k === "category") return p.category === v;
        return p.attributes?.[k] === v;
      }),
    );
  }, [results, filters]);

  const hasSearched = !!(text.data || image.data || multi.data);

  return (
    <>
      <section className="hero-grad border-b">
        <div className="container py-16 md:py-24">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mx-auto max-w-3xl text-center"
          >
            <div className="mx-auto mb-4 inline-flex items-center gap-2 rounded-full border bg-background/80 px-3 py-1 text-xs font-medium backdrop-blur">
              <Sparkles className="h-3.5 w-3.5 text-violet-500" />
              Multimodal Product Catalogue Intelligence
            </div>
            <h1 className="text-4xl font-bold tracking-tight md:text-6xl">
              Find the right product with{" "}
              <span className="bg-gradient-to-r from-indigo-500 via-violet-500 to-fuchsia-500 bg-clip-text text-transparent">
                words, images, or both
              </span>
            </h1>
            <p className="mx-auto mt-5 max-w-xl text-lg text-muted-foreground">
              Describe what you want, upload a reference photo, or combine the two for pixel-perfect matches.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mx-auto mt-10 max-w-3xl rounded-2xl border bg-card p-4 shadow-xl md:p-6"
          >
            <Tabs defaultValue="text" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="text">
                  <Type className="mr-2 h-4 w-4" /> Text
                </TabsTrigger>
                <TabsTrigger value="image">
                  <ImageIcon className="mr-2 h-4 w-4" /> Image
                </TabsTrigger>
                <TabsTrigger value="multi">
                  <Wand2 className="mr-2 h-4 w-4" /> Multimodal
                </TabsTrigger>
              </TabsList>

              <TabsContent value="text">
                <SearchBar onSubmit={(q) => text.mutate(q)} loading={text.isPending} />
              </TabsContent>

              <TabsContent value="image" className="space-y-3">
                <ImageUploader value={imgFile} onChange={setImgFile} />
                <Button
                  variant="gradient"
                  size="lg"
                  className="w-full"
                  disabled={!imgFile || image.isPending}
                  onClick={() => imgFile && image.mutate(imgFile)}
                >
                  Search by image
                </Button>
              </TabsContent>

              <TabsContent value="multi">
                <MultimodalSearchForm
                  loading={multi.isPending}
                  onSubmit={(d) => multi.mutate(d)}
                />
              </TabsContent>
            </Tabs>
          </motion.div>
        </div>
      </section>

      <section className="container py-12">
        <div className="flex flex-col gap-8 lg:flex-row">
          {hasSearched && results.length > 0 && (
            <Sidebar
              products={results}
              selected={filters}
              onChange={(k, v) => setFilters((f) => ({ ...f, [k]: v }))}
            />
          )}
          <div className="flex-1">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-2xl font-semibold">
                {hasSearched ? "Results" : "Try a search"}
              </h2>
              {hasSearched && results.length > 0 && (
                <p className="text-sm text-muted-foreground">
                  {filtered.length} of {results.length} products
                </p>
              )}
            </div>

            {activeMutation ? (
              <ProductGridSkeleton />
            ) : error ? (
              <ErrorState
                description={(error as Error).message}
                onRetry={() => {
                  text.reset();
                  image.reset();
                  multi.reset();
                }}
              />
            ) : !hasSearched ? (
              <EmptyState
                title="Your AI-powered catalogue awaits"
                description="Pick a modality above and we'll surface the closest matches with semantic scores."
              />
            ) : filtered.length === 0 ? (
              <EmptyState title="No matches" description="Try different filters or another query." />
            ) : (
              <ProductGrid products={filtered} />
            )}
          </div>
        </div>
      </section>
    </>
  );
}
