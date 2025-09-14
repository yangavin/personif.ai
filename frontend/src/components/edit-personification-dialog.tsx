"use client";

import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/src/components/ui/dialog";
import { Button } from "@/src/components/ui/button";
import { Input } from "@/src/components/ui/input";
import { Textarea } from "@/src/components/ui/textarea";
import { Personification } from "@/types/personification";

interface EditPersonificationDialogProps {
  personification: Personification | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (updatedPersonification: Personification) => void;
}

export function EditPersonificationDialog({
  personification,
  isOpen,
  onClose,
  onSave,
}: EditPersonificationDialogProps) {
  const [formData, setFormData] = useState<Personification | null>(null);

  React.useEffect(() => {
    if (personification) {
      setFormData({ ...personification });
    }
  }, [personification]);

  if (!formData) return null;

  const handleSave = () => {
    onSave(formData);
    onClose();
  };

  const updateField = (
    field: keyof Personification,
    value: string | string[]
  ) => {
    setFormData((prev) => {
      if (!prev) return prev;
      return { ...prev, [field]: value };
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Personification</DialogTitle>
          <DialogDescription>
            Update the details, style, prompts, and sources for this
            personification.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Name</label>
              <Input
                value={formData.name}
                onChange={(e) => updateField("name", e.target.value)}
                placeholder="Personification name"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Status</label>
              <select
                value={formData.status}
                onChange={(e) => updateField("status", e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="training">Training</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium">Content</label>
            <Textarea
              value={formData.content}
              onChange={(e) => updateField("content", e.target.value)}
              placeholder="Enter description, style, and prompts for this personification"
              rows={6}
            />
            <p className="text-xs text-gray-500 mt-1">
              Include description, speaking style, and prompts all in one field.
            </p>
          </div>

          <div>
            <label className="text-sm font-medium">Profile Picture URL</label>
            <Input
              value={formData.profilePic || ""}
              onChange={(e) => updateField("profilePic", e.target.value)}
              placeholder="Enter URL for profile picture"
            />
          </div>

          <div>
            <label className="text-sm font-medium">ElevenLabs Voice ID</label>
            <Input
              value={formData.elevenLabsId || ""}
              onChange={(e) => updateField("elevenLabsId", e.target.value)}
              placeholder="Enter ElevenLabs voice ID"
            />
          </div>

          <div>
            <label className="text-sm font-medium">Quotes</label>
            <Textarea
              value={formData.quotes ? formData.quotes.join("\n") : ""}
              onChange={(e) =>
                updateField(
                  "quotes",
                  e.target.value.split("\n").filter(Boolean)
                )
              }
              placeholder="Enter quotes, one per line"
              rows={4}
            />
            <p className="text-xs text-gray-500 mt-1">
              Enter one quote per line. These will be displayed on the
              personification card.
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave}>Save Changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
