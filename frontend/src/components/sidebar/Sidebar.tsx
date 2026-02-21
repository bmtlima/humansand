"use client";

import { ConversationSummary } from "@/lib/types";
import { NewChatButton } from "./NewChatButton";
import { ConversationItem } from "./ConversationItem";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Database } from "lucide-react";

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
    <div className="flex h-full w-64 flex-col border-r bg-muted/30">
      <div className="p-3">
        <h1 className="mb-3 px-2 text-lg font-bold">HumanSand</h1>
        <NewChatButton onClick={onNewChat} />
      </div>

      <Separator />

      <ScrollArea className="flex-1 px-3 py-2">
        <div className="space-y-1">
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
            <p className="px-2 py-4 text-center text-xs text-muted-foreground">
              No conversations yet
            </p>
          )}
        </div>
      </ScrollArea>

      <Separator />

      <div className="p-3">
        <Button
          variant="ghost"
          className="w-full justify-start gap-2 text-sm"
          onClick={() => window.open("/personal-info", "_blank")}
        >
          <Database className="h-4 w-4" />
          Personal Information
        </Button>
      </div>
    </div>
  );
}
