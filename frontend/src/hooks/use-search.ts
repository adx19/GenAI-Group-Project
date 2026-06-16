"use client";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  searchText,
  searchImage,
  searchMultimodal,
  getProduct,
  getAnalytics,
} from "@/services/products";

export const useTextSearch = () =>
  useMutation({ mutationFn: (query: string) => searchText(query) });

export const useImageSearch = () =>
  useMutation({ mutationFn: (image: File) => searchImage(image) });

export const useMultimodalSearch = () =>
  useMutation({
    mutationFn: ({ image, query }: { image: File; query: string }) =>
      searchMultimodal(image, query),
  });

export const useProduct = (id: string | number) =>
  useQuery({ queryKey: ["product", id], queryFn: () => getProduct(id), enabled: !!id });

export const useAnalytics = () =>
  useQuery({ queryKey: ["analytics"], queryFn: () => getAnalytics() });
