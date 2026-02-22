"use client";

import { ConversationSummary } from "@/lib/types";
import { NewChatButton } from "./NewChatButton";
import { ConversationItem } from "./ConversationItem";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Database } from "lucide-react";
import Image from "next/image";

interface SidebarProps {
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  onRenameConversation: (id: string, title: string) => void;
}

export function Sidebar({
  conversations,
  activeConversationId,
  onNewChat,
  onSelectConversation,
  onDeleteConversation,
  onRenameConversation,
}: SidebarProps) {
  return (
    <div className="flex h-full w-[280px] max-w-[78vw] shrink-0 flex-col border-r border-slate-200/80 bg-white/85 dark:border-slate-800 dark:bg-slate-900/85">
      <div className="p-4">
          <div className="mb-4 rounded-xl bg-gradient-to-br from-indigo-600 to-blue-500 px-4 py-3 text-white shadow-md dark:from-indigo-500 dark:to-blue-400">

          <div className="flex items-center gap-2">
            <Image src="/linkmate-no-bg.png" alt="LinkMate" width={28} height={28} />
            <h1 className="text-lg font-semibold tracking-tight">LinkMate</h1>
          </div>
          <p className="mt-1 text-xs text-indigo-100">AI Coordination Workspace</p>
        </div>
        <NewChatButton onClick={onNewChat} />
      </div>

      <Separator />

      <ScrollArea className="flex-1 px-3 py-3">
        <div className="space-y-1.5">
          {conversations.map((conv) => (
            <ConversationItem
              key={conv.id}
              conversation={conv}
              isActive={conv.id === activeConversationId}
              onClick={() => onSelectConversation(conv.id)}
              onDelete={() => onDeleteConversation(conv.id)}
              onRename={(title) => onRenameConversation(conv.id, title)}
            />
          ))}
          {conversations.length === 0 && (
            <p className="rounded-lg border border-dashed border-slate-300 px-3 py-6 text-center text-xs text-slate-500 dark:border-slate-700 dark:text-slate-400">
              No conversations yet.
              <br />
              Start one to see history here.
            </p>
          )}
        </div>
      </ScrollArea>

      <Separator />

      <div className="p-3">
        <Button
          variant="ghost"
          className="w-full justify-start gap-2 rounded-lg text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
          onClick={() => window.open("/personal-info", "_blank")}
        >
          <Database className="h-4 w-4" />
          Personal Information
        </Button>
      </div>
    </div>
  );
}
