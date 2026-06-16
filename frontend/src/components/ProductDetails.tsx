"use client";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { AttributeBadges } from "./AttributeBadges";
import type { Product } from "@/types";

export function ProductDetails({ product }: { product: Product }) {
  return (
    <div className="grid gap-10 md:grid-cols-2">
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="overflow-hidden rounded-2xl border bg-muted"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={product.image_url} alt={product.name} className="aspect-square w-full object-cover" />
      </motion.div>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.05 }}
        className="flex flex-col gap-5"
      >
        <Badge variant="outline" className="w-fit uppercase tracking-wider">
          {product.category}
        </Badge>
        <h1 className="text-3xl font-bold leading-tight md:text-4xl">{product.name}</h1>
        <p className="text-lg leading-relaxed text-muted-foreground">{product.description}</p>
        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            Extracted Attributes
          </h3>
          <AttributeBadges attributes={product.attributes} />
        </div>
      </motion.div>
    </div>
  );
}
