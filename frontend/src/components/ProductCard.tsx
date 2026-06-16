"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Product } from "@/types";

export function ProductCard({ product, index = 0 }: { product: Product; index?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.04 }}
    >
      <Link href={`/products/${product.id}`} className="group block">
        <Card className="overflow-hidden transition-all hover:shadow-lg hover:-translate-y-0.5">
          <div className="relative aspect-square overflow-hidden bg-muted">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={product.image_url}
              alt={product.name}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
            {product.score !== undefined && (
              <div className="absolute right-2 top-2 flex items-center gap-1 rounded-full bg-background/90 px-2 py-1 text-xs font-semibold shadow">
                <Sparkles className="h-3 w-3 text-violet-500" />
                {(product.score * 100).toFixed(0)}%
              </div>
            )}
          </div>
          <CardContent className="p-4">
            <Badge variant="outline" className="mb-2 text-[10px] uppercase tracking-wider">
              {product.category}
            </Badge>
            <h3 className="line-clamp-1 font-semibold">{product.name}</h3>
            <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{product.description}</p>
          </CardContent>
        </Card>
      </Link>
    </motion.div>
  );
}
