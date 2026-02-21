"use client";

import { useState, useRef, useEffect } from "react";
import { ConversationSummary } from "@/lib/types";
import { MoreVertical, Trash2, Pencil, MessageSquare } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface ConversationItemProps {
  conversation: ConversationSummary;
  isActive: boolean;
  onClick: () => void;
  onDelete: () => void;
  onRename: (title: string) => void;
}

export function ConversationItem({
  conversation,
  isActive,
  onClick,
  onDelete,
  onRename,
}: ConversationItemProps) {
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(conversation.title);
  const [menuOpen, setMenuOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isRenaming) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [isRenaming]);

  const handleRenameSubmit = () => {
    const trimmed = renameValue.trim();
    if (trimmed && trimmed !== conversation.title) {
      onRename(trimmed);
    } else {
      setRenameValue(conversation.title);
    }
    setIsRenaming(false);
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => !isRenaming && onClick()}
      onKeyDown={(e) => {
        if (!isRenaming && (e.key === "Enter" || e.key === " ")) onClick();
      }}
      className={`group relative flex w-full cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-muted ${
        isActive ? "bg-muted" : ""
      }`}
    >
      <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        {isRenaming ? (
          <input
            ref={inputRef}
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onBlur={handleRenameSubmit}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleRenameSubmit();
              if (e.key === "Escape") {
                setRenameValue(conversation.title);
                setIsRenaming(false);
              }
            }}
            onClick={(e) => e.stopPropagation()}
            className="w-full rounded border bg-background px-1 py-0.5 text-sm font-medium outline-none focus:ring-1 focus:ring-ring"
          />
        ) : (
          <p className="truncate pr-6 font-medium">{conversation.title}</p>
        )}
      </div>

      {/* Absolutely positioned on the right so ScrollArea's display:table can't push it offscreen */}
      <div
        className={`absolute right-1 top-1/2 -translate-y-1/2 ${
          menuOpen ? "block" : "hidden group-hover:block"
        }`}
      >
        <DropdownMenu open={menuOpen} onOpenChange={setMenuOpen}>
          <DropdownMenuTrigger asChild>
            <button
              onClick={(e) => e.stopPropagation()}
              className="rounded-full p-1 text-muted-foreground hover:bg-muted-foreground/10"
            >
              <MoreVertical className="h-4 w-4" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" side="bottom">
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation();
                setRenameValue(conversation.title);
                setIsRenaming(true);
              }}
            >
              <Pencil className="mr-2 h-4 w-4" />
              Rename
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
