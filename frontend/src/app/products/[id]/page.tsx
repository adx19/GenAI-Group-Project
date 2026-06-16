"use client";
import Link from "next/link";
import { use } from "react";
import { ArrowLeft } from "lucide-react";
import { ProductDetails } from "@/components/ProductDetails";
import { DetailsSkeleton } from "@/components/LoadingSkeleton";
import { ErrorState } from "@/components/ErrorState";
import { useProduct } from "@/hooks/use-search";

export default function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, isLoading, error, refetch } = useProduct(id);

  return (
    <div className="container py-10">
      <Link
        href="/"
        className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> Back to discovery
      </Link>
      {isLoading ? (
        <DetailsSkeleton />
      ) : error ? (
        <ErrorState description={(error as Error).message} onRetry={() => refetch()} />
      ) : data ? (
        <ProductDetails product={data} />
      ) : null}
    </div>
  );
}
