"use client";
import { Activity, Type, Image as ImageIcon, Wand2, MousePointerClick, LogOut, SearchX } from "lucide-react";
import { AnalyticsCard } from "@/components/AnalyticsCards";
import { AnalyticsCharts } from "@/components/AnalyticsCharts";
import { AnalyticsSkeleton } from "@/components/LoadingSkeleton";
import { ErrorState } from "@/components/ErrorState";
import { useAnalytics } from "@/hooks/use-search";
import { formatPercent } from "@/lib/utils";

export default function AnalyticsPage() {
  const { data, isLoading, error, refetch } = useAnalytics();

  return (
    <div className="container py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        <p className="mt-1 text-muted-foreground">
          Real-time intelligence on how shoppers discover your catalogue.
        </p>
      </div>

      {isLoading ? (
        <AnalyticsSkeleton />
      ) : error ? (
        <ErrorState description={(error as Error).message} onRetry={() => refetch()} />
      ) : data ? (
        <div className="space-y-8">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <AnalyticsCard
              label="Total Searches"
              value={data.total_searches.toLocaleString()}
              icon={Activity}
              accent="bg-indigo-500"
              index={0}
            />
            <AnalyticsCard
              label="Text Searches"
              value={data.text_searches.toLocaleString()}
              icon={Type}
              accent="bg-violet-500"
              hint={`${formatPercent(data.text_searches / data.total_searches)} of total`}
              index={1}
            />
            <AnalyticsCard
              label="Image Searches"
              value={data.image_searches.toLocaleString()}
              icon={ImageIcon}
              accent="bg-fuchsia-500"
              hint={`${formatPercent(data.image_searches / data.total_searches)} of total`}
              index={2}
            />
            <AnalyticsCard
              label="Multimodal Searches"
              value={data.multimodal_searches.toLocaleString()}
              icon={Wand2}
              accent="bg-amber-500"
              hint={`${formatPercent(data.multimodal_searches / data.total_searches)} of total`}
              index={3}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <AnalyticsCard
              label="Click-Through Rate"
              value={formatPercent(data.ctr)}
              icon={MousePointerClick}
              accent="bg-emerald-500"
              hint="Sessions that clicked a result"
            />
            <AnalyticsCard
              label="Abandonment Rate"
              value={formatPercent(data.abandonment_rate)}
              icon={LogOut}
              accent="bg-rose-500"
              hint="Search → exit without click"
            />
            <AnalyticsCard
              label="Zero-Result Searches"
              value={data.zero_result_searches}
              icon={SearchX}
              accent="bg-slate-500"
              hint="Queries returning no products"
            />
          </div>

          <AnalyticsCharts data={data} />
        </div>
      ) : null}
    </div>
  );
}
