"use client";

import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

interface NewChatButtonProps {
  onClick: () => void;
}

export function NewChatButton({ onClick }: NewChatButtonProps) {
  return (
    <Button
      variant="default"
      className="w-full justify-start gap-2 rounded-xl bg-slate-900 text-white shadow-sm hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
      onClick={onClick}
    >
      <Plus className="h-4 w-4" />
      New chat
    </Button>
  );
}
