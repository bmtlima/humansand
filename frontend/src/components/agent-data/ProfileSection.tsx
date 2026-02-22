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
    <div className="space-y-5">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">Name</p>
        <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">{profile.name}</p>
      </div>

      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">Role</p>
        {editingRole ? (
          <div className="mt-1 flex items-center gap-1">
            <Input
              value={roleValue}
              onChange={(e) => setRoleValue(e.target.value)}
              className="h-8 border-slate-200 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              onKeyDown={(e) => e.key === "Enter" && saveRole()}
              autoFocus
            />
            <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-600 dark:text-slate-300" onClick={saveRole}>
              <Check className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-slate-600 dark:text-slate-300"
              onClick={() => setEditingRole(false)}
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>
        ) : (
          <div className="group mt-1 flex items-center gap-1">
            <p className="text-sm text-slate-700 dark:text-slate-300">{profile.role}</p>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-slate-500 opacity-0 transition-opacity group-hover:opacity-100"
              onClick={() => {
                setRoleValue(profile.role);
                setEditingRole(true);
              }}
            >
              <Pencil className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}
      </div>

      <div>
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">Skills</p>
        <div className="flex flex-wrap gap-2">
          {profile.skills.map((skill) => (
            <Badge
              key={skill}
              variant="secondary"
              className="group/badge gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              {skill}
              <button
                onClick={() => removeSkill(skill)}
                className="ml-0.5 opacity-0 transition-opacity hover:text-destructive group-hover/badge:opacity-100"
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
                className="h-7 w-28 border-slate-200 text-xs dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                placeholder="Skill name"
                onKeyDown={(e) => e.key === "Enter" && addSkill()}
                autoFocus
              />
              <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-600 dark:text-slate-300" onClick={addSkill}>
                <Check className="h-3.5 w-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-slate-600 dark:text-slate-300"
                onClick={() => setAddingSkill(false)}
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            </div>
          ) : (
            <button
              onClick={() => setAddingSkill(true)}
              className="flex h-7 items-center gap-1 rounded-full border border-dashed border-slate-300 px-2.5 text-xs text-slate-500 transition hover:border-slate-400 hover:text-slate-700 dark:border-slate-700 dark:text-slate-400 dark:hover:border-slate-500 dark:hover:text-slate-200"
            >
              <Plus className="h-3 w-3" /> Add
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
