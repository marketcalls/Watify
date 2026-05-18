"use client";

import useSWR from "swr";
import { api, type Health } from "@/lib/api";

const KEY = "/api/health";

export function useHealth() {
  const { data, error, isLoading } = useSWR<Health>(
    KEY,
    () => api.get<Health>(KEY),
    {
      refreshInterval: 3000,
      revalidateOnFocus: false,
      shouldRetryOnError: true,
      errorRetryInterval: 3000,
    }
  );

  return {
    health: data,
    isLoading,
    isError: Boolean(error),
    error,
  };
}
