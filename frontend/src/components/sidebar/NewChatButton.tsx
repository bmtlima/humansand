"use client";

import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

interface NewChatButtonProps {
  onClick: () => void;
}

export function NewChatButton({ onClick }: NewChatButtonProps) {
  return (
    <Button
      variant="outline"
      className="w-full justify-start gap-2"
      onClick={onClick}
    >
      <Plus className="h-4 w-4" />
      New chat
    </Button>
  );
}
