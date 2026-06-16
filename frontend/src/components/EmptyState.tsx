import { SearchX } from "lucide-react";

export function EmptyState({
  title = "No results yet",
  description = "Try a text query, drop an image, or combine both.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed bg-card px-6 py-20 text-center">
      <div className="mb-4 rounded-full bg-accent p-3 text-accent-foreground">
        <SearchX className="h-6 w-6" />
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-1 max-w-md text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
