"use client";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

export type AnalyticsCardProps = {
  label: string;
  value: string | number;
  icon: LucideIcon;
  hint?: string;
  accent?: string;
  index?: number;
};

export function AnalyticsCard({ label, value, icon: Icon, hint, accent, index = 0 }: AnalyticsCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <Card className="relative overflow-hidden">
        <div className={cn("absolute inset-x-0 top-0 h-1", accent ?? "bg-primary")} />
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</p>
              <p className="mt-2 text-3xl font-bold">{value}</p>
              {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
            </div>
            <div className="rounded-lg bg-accent p-2.5 text-accent-foreground">
              <Icon className="h-5 w-5" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
