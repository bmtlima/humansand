"use client";

import { useState, useCallback, useEffect } from "react";
import { AgentData } from "@/lib/types";
import { getAgentData, updateAgentData } from "@/lib/api";

export function useAgentData(userName: string) {
  const [data, setData] = useState<AgentData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const result = await getAgentData(userName);
      setData(result);
    } catch (err) {
      console.error("Failed to load agent data:", err);
    } finally {
      setIsLoading(false);
    }
  }, [userName]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const updateProfile = useCallback(
    async (profile: { role?: string; skills?: string[] }) => {
      if (!data) return;
      const prev = data;
      setData({ ...data, profile: { ...data.profile, ...profile } });
      try {
        await updateAgentData(userName, { profile });
      } catch (err) {
        console.error("Failed to update profile:", err);
        setData(prev);
      }
    },
    [data, userName]
  );

  return {
    data,
    isLoading,
    refresh,
    updateProfile,
  };
}
