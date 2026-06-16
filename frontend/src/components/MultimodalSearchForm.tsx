"use client";
import { useState } from "react";
import { ImageUploader } from "./ImageUploader";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Loader2, Wand2 } from "lucide-react";

type Props = {
  loading?: boolean;
  onSubmit: (data: { image: File; query: string }) => void;
};

export function MultimodalSearchForm({ loading, onSubmit }: Props) {
  const [image, setImage] = useState<File | null>(null);
  const [query, setQuery] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (image && query.trim()) onSubmit({ image, query: query.trim() });
      }}
      className="grid gap-4 md:grid-cols-2"
    >
      <ImageUploader value={image} onChange={setImage} label="Add a reference image" />
      <div className="flex flex-col gap-3">
        <Input
          placeholder="Refine with text, e.g. 'in walnut wood, more minimal'"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="h-12 text-base"
        />
        <Button
          type="submit"
          variant="gradient"
          size="lg"
          disabled={!image || !query.trim() || loading}
          className="w-full"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <>
              <Wand2 className="h-4 w-4" /> Run multimodal search
            </>
          )}
        </Button>
        <p className="text-xs text-muted-foreground">
          Combine vision and language for the most precise matches.
        </p>
      </div>
    </form>
  );
}
