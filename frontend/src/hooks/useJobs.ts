"use client";

import useSWR, { mutate } from "swr";
import {
  jobs,
  type SendJobDetail,
  type SendJobRead,
  type SendRequest,
} from "@/lib/api";

const LIST_KEY = "/api/jobs";

export function useJobs() {
  const { data, error, isLoading } = useSWR<SendJobRead[]>(
    LIST_KEY,
    () => jobs.list(),
    { refreshInterval: 3000, revalidateOnFocus: false }
  );

  async function createSend(body: SendRequest): Promise<SendJobRead> {
    const job = await jobs.create(body);
    await mutate(LIST_KEY);
    return job;
  }

  async function cancelJob(id: number): Promise<void> {
    await jobs.cancel(id);
    await mutate(LIST_KEY);
    await mutate(`/api/jobs/${id}`);
  }

  return {
    list: data ?? [],
    isLoading,
    isError: Boolean(error),
    error,
    createSend,
    cancelJob,
    refresh: () => mutate(LIST_KEY),
  };
}

export function useJobDetail(id: number | null) {
  const key = id == null ? null : `/api/jobs/${id}`;
  const { data, error, isLoading } = useSWR<SendJobDetail>(
    key,
    () => jobs.get(id!),
    {
      refreshInterval: (latest) => {
        const phase = (latest as SendJobDetail | undefined)?.status;
        if (phase === "running" || phase === "pending" || phase === "scheduled")
          return 2000;
        return 0;
      },
      revalidateOnFocus: false,
    }
  );

  return {
    detail: data,
    isLoading,
    isError: Boolean(error),
    error,
    refresh: () => mutate(key),
  };
}
