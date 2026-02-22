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
      className={`group relative flex w-full cursor-pointer items-center gap-2 rounded-xl border px-3 py-2.5 text-left text-sm transition-all ${
        isActive
          ? "border-slate-300 bg-slate-100/90 shadow-sm dark:border-slate-700 dark:bg-slate-800/90"
          : "border-transparent hover:border-slate-200 hover:bg-slate-100/70 dark:hover:border-slate-700 dark:hover:bg-slate-800/70"
      }`}
    >
      <MessageSquare
        className={`h-4 w-4 shrink-0 ${
          isActive ? "text-slate-700 dark:text-slate-200" : "text-slate-400 dark:text-slate-500"
        }`}
      />
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
          <p className="truncate font-medium text-slate-700 dark:text-slate-200">{conversation.title}</p>
        )}
      </div>
      <div className={`shrink-0 ${menuOpen ? "block" : "hidden group-hover:block"}`}>
        <DropdownMenu open={menuOpen} onOpenChange={setMenuOpen}>
          <DropdownMenuTrigger asChild>
            <button
              onClick={(e) => e.stopPropagation()}
              className="rounded-full p-1 text-muted-foreground hover:bg-muted-foreground/10"
            >
              <MoreVertical className="h-4 w-4" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" side="bottom">
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
