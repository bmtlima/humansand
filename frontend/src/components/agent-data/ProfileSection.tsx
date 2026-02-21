"use client";

import { useState } from "react";
import { Profile } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Pencil, Check, X, Plus } from "lucide-react";

interface ProfileSectionProps {
  profile: Profile;
  onUpdate: (profile: { role?: string; skills?: string[] }) => Promise<void>;
}

export function ProfileSection({ profile, onUpdate }: ProfileSectionProps) {
  const [editingRole, setEditingRole] = useState(false);
  const [roleValue, setRoleValue] = useState(profile.role);
  const [addingSkill, setAddingSkill] = useState(false);
  const [newSkill, setNewSkill] = useState("");

  const saveRole = async () => {
    if (roleValue.trim() && roleValue !== profile.role) {
      await onUpdate({ role: roleValue.trim() });
    }
    setEditingRole(false);
  };

  const removeSkill = async (skill: string) => {
    await onUpdate({ skills: profile.skills.filter((s) => s !== skill) });
  };

  const addSkill = async () => {
    if (newSkill.trim() && !profile.skills.includes(newSkill.trim())) {
      await onUpdate({ skills: [...profile.skills, newSkill.trim()] });
      setNewSkill("");
      setAddingSkill(false);
    }
  };

  return (
    <div className="space-y-3">
      <div>
        <p className="text-muted-foreground text-xs">Name</p>
        <p className="text-sm font-medium">{profile.name}</p>
      </div>

      <div>
        <p className="text-muted-foreground text-xs">Role</p>
        {editingRole ? (
          <div className="flex items-center gap-1">
            <Input
              value={roleValue}
              onChange={(e) => setRoleValue(e.target.value)}
              className="h-7 text-sm"
              onKeyDown={(e) => e.key === "Enter" && saveRole()}
              autoFocus
            />
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={saveRole}>
              <Check className="h-3 w-3" />
            </Button>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setEditingRole(false)}>
              <X className="h-3 w-3" />
            </Button>
          </div>
        ) : (
          <div className="group flex items-center gap-1">
            <p className="text-sm">{profile.role}</p>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 opacity-0 group-hover:opacity-100"
              onClick={() => { setRoleValue(profile.role); setEditingRole(true); }}
            >
              <Pencil className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>

      <div>
        <p className="text-muted-foreground mb-1 text-xs">Skills</p>
        <div className="flex flex-wrap gap-1.5">
          {profile.skills.map((skill) => (
            <Badge key={skill} variant="secondary" className="group/badge gap-1 pr-1">
              {skill}
              <button
                onClick={() => removeSkill(skill)}
                className="hover:text-destructive ml-0.5 opacity-0 group-hover/badge:opacity-100"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          {addingSkill ? (
            <div className="flex items-center gap-1">
              <Input
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                className="h-6 w-24 text-xs"
                placeholder="Skill name"
                onKeyDown={(e) => e.key === "Enter" && addSkill()}
                autoFocus
              />
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={addSkill}>
                <Check className="h-3 w-3" />
              </Button>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setAddingSkill(false)}>
                <X className="h-3 w-3" />
              </Button>
            </div>
          ) : (
            <button
              onClick={() => setAddingSkill(true)}
              className="border-muted-foreground text-muted-foreground hover:border-foreground hover:text-foreground flex h-6 items-center gap-1 rounded-md border border-dashed px-2 text-xs"
            >
              <Plus className="h-3 w-3" /> Add
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
