"use client";

import { useAgentData } from "@/hooks/useAgentData";
import { ProfileSection } from "@/components/agent-data/ProfileSection";
import { CalendarSection } from "@/components/agent-data/CalendarSection";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { User, Calendar } from "lucide-react";

const AGENT = "Alice";

export default function PersonalInfoPage() {
  const { data, isLoading, updateProfile } = useAgentData(AGENT);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white px-4 py-8 dark:from-slate-950 dark:to-slate-900 sm:px-6 sm:py-10">
      <div className="mx-auto mb-4 flex max-w-3xl justify-end">
        <ThemeToggle />
      </div>
      <div className="mx-auto max-w-3xl">
        <div className="mb-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
            Personal Information
          </h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            This is the data {AGENT}&apos;s agent has access to.
          </p>
        </div>

        {isLoading || !data ? (
          <div className="space-y-6">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-28 w-full rounded-xl" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-36 w-full rounded-xl" />
          </div>
        ) : (
          <div className="space-y-8">
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
              <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-900 dark:text-slate-100">
                <User className="h-5 w-5 text-indigo-600" />
                Profile
              </h2>
              <ProfileSection profile={data.profile} onUpdate={updateProfile} />
            </section>

            <Separator />

            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
              <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-900 dark:text-slate-100">
                <Calendar className="h-5 w-5 text-indigo-600" />
                Calendar
              </h2>
              <CalendarSection calendar={data.calendar} />
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
