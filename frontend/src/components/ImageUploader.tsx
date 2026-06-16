"use client";
import { useCallback, useRef, useState } from "react";
import { ImagePlus, X } from "lucide-react";
import { cn } from "@/lib/utils";

type Props = {
  value: File | null;
  onChange: (file: File | null) => void;
  className?: string;
  label?: string;
};

export function ImageUploader({ value, onChange, className, label = "Drop image or click to upload" }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const set = useCallback(
    (file: File | null) => {
      if (preview) URL.revokeObjectURL(preview);
      if (file) setPreview(URL.createObjectURL(file));
      else setPreview(null);
      onChange(file);
    },
    [onChange, preview],
  );

  return (
    <div className={className}>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const f = e.dataTransfer.files?.[0];
          if (f) set(f);
        }}
        className={cn(
          "group relative flex aspect-video w-full cursor-pointer flex-col items-center justify-center overflow-hidden rounded-xl border-2 border-dashed bg-muted/30 transition-all",
          dragging ? "border-primary bg-primary/5" : "hover:bg-muted/50",
        )}
      >
        {preview ? (
          <>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={preview} alt="preview" className="h-full w-full object-cover" />
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                set(null);
              }}
              className="absolute right-2 top-2 rounded-full bg-background/90 p-1.5 shadow hover:bg-background"
            >
              <X className="h-4 w-4" />
            </button>
          </>
        ) : (
          <div className="flex flex-col items-center gap-2 text-muted-foreground">
            <div className="rounded-full bg-background p-3 shadow-sm">
              <ImagePlus className="h-6 w-6" />
            </div>
            <p className="text-sm font-medium">{label}</p>
            <p className="text-xs">PNG, JPG up to 10MB</p>
          </div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          hidden
          onChange={(e) => set(e.target.files?.[0] ?? null)}
        />
      </div>
      {value && <p className="mt-2 text-xs text-muted-foreground">{value.name}</p>}
    </div>
  );
}
