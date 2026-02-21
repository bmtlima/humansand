"use client";

import { ConversationSummary } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Trash2, MessageSquare } from "lucide-react";

interface ConversationItemProps {
  conversation: ConversationSummary;
  isActive: boolean;
  onClick: () => void;
  onDelete: () => void;
}

export function ConversationItem({
  conversation,
  isActive,
  onClick,
  onDelete,
}: ConversationItemProps) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onClick(); }}
      className={`group flex w-full cursor-pointer items-start gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-muted ${
        isActive ? "bg-muted" : ""
      }`}
    >
      <MessageSquare className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium">{conversation.title}</p>
        <Badge variant="secondary" className="mt-1 text-[10px]">
          {conversation.agent}
        </Badge>
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        className="mt-0.5 hidden shrink-0 rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive group-hover:block"
      >
        <Trash2 className="h-3 w-3" />
      </button>
    </div>
  );
}
