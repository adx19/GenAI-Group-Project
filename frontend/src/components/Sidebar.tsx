"use client";
import { Filter } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { Product } from "@/types";
import { useMemo } from "react";

type Props = {
  products: Product[];
  selected: Record<string, string | null>;
  onChange: (key: string, value: string | null) => void;
};

const FACETS = ["category", "color", "material", "style", "shape"] as const;

export function Sidebar({ products, selected, onChange }: Props) {
  const facets = useMemo(() => {
    const result: Record<string, Set<string>> = {};
    FACETS.forEach((f) => (result[f] = new Set()));
    products.forEach((p) => {
      if (p.category) result.category.add(p.category);
      Object.entries(p.attributes ?? {}).forEach(([k, v]) => {
        if (v && result[k]) result[k].add(v);
      });
    });
    return result;
  }, [products]);

  return (
    <aside className="sticky top-20 hidden h-fit w-64 shrink-0 rounded-xl border bg-card p-5 lg:block">
      <div className="mb-4 flex items-center gap-2">
        <Filter className="h-4 w-4" />
        <h3 className="text-sm font-semibold">Filters</h3>
      </div>
      <div className="space-y-5">
        {FACETS.map((facet) => {
          const values = Array.from(facets[facet]);
          if (!values.length) return null;
          return (
            <div key={facet}>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {facet}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {values.map((v) => {
                  const active = selected[facet] === v;
                  return (
                    <button
                      key={v}
                      onClick={() => onChange(facet, active ? null : v)}
                      className="focus:outline-none"
                    >
                      <Badge variant={active ? "default" : "outline"}>{v}</Badge>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
