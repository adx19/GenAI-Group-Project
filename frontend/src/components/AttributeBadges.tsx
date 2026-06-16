import { Badge } from "@/components/ui/badge";
import type { ProductAttributes } from "@/types";

export function AttributeBadges({ attributes }: { attributes?: ProductAttributes }) {
  if (!attributes) return null;
  const entries = Object.entries(attributes).filter(([, v]) => !!v);
  if (!entries.length) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {entries.map(([k, v]) => (
        <Badge key={k} variant="secondary" className="px-3 py-1 text-xs">
          <span className="mr-1 text-muted-foreground capitalize">{k}:</span>
          <span className="font-medium">{v}</span>
        </Badge>
      ))}
    </div>
  );
}
