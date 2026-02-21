"use client";

import { useAgentData } from "@/hooks/useAgentData";
import { ProfileSection } from "@/components/agent-data/ProfileSection";
import { CalendarSection } from "@/components/agent-data/CalendarSection";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { User, Calendar } from "lucide-react";

const AGENT = "Alice";

export default function PersonalInfoPage() {
  const {
    data,
    isLoading,
    updateProfile,
  } = useAgentData(AGENT);

  return (
    <div className="mx-auto max-w-xl px-6 py-10">
      <h1 className="mb-6 text-2xl font-bold">Personal Information</h1>
      <p className="text-muted-foreground mb-8 text-sm">
        This is the data {AGENT}&apos;s agent has access to.
      </p>

      {isLoading || !data ? (
        <div className="space-y-6">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-36 w-full" />
        </div>
      ) : (
        <div className="space-y-8">
          <section>
            <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
              <User className="h-5 w-5" />
              Profile
            </h2>
            <ProfileSection profile={data.profile} onUpdate={updateProfile} />
          </section>

          <Separator />

          <section>
            <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
              <Calendar className="h-5 w-5" />
              Calendar
            </h2>
            <CalendarSection calendar={data.calendar} />
          </section>
        </div>
      )}
    </div>
  );
}
