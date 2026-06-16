"use client";
import { Search, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState, FormEvent } from "react";

type Props = {
  onSubmit: (query: string) => void;
  loading?: boolean;
  defaultValue?: string;
  placeholder?: string;
};

export function SearchBar({ onSubmit, loading, defaultValue = "", placeholder }: Props) {
  const [value, setValue] = useState(defaultValue);
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (value.trim()) onSubmit(value.trim());
  };
  return (
    <form onSubmit={submit} className="flex w-full gap-2">
      <div className="relative flex-1">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder ?? "Search products, e.g. 'comfortable black office chair'"}
          className="h-12 pl-9 text-base"
        />
      </div>
      <Button type="submit" size="lg" variant="gradient" disabled={loading}>
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
      </Button>
    </form>
  );
}
