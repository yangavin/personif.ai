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
import { Upload, X } from "lucide-react";

interface NewPersonificationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (
    personification: Omit<Personification, "id" | "createdAt" | "updatedAt">
  ) => void;
}

export function NewPersonificationDialog({
  isOpen,
  onClose,
  onSave,
}: NewPersonificationDialogProps) {
  const [formData, setFormData] = useState({
    name: "",
    content: "",
    quotes: [] as string[],
    profilePic: "",
    elevenLabsId: "",
    status: "inactive" as const,
  });

  const [previewImage, setPreviewImage] = useState<string | null>(null);

  const handleSave = () => {
    if (!formData.name.trim()) return;

    onSave(formData);
    handleClose();
  };

  const handleClose = () => {
    setFormData({
      name: "",
      content: "",
      quotes: [],
      profilePic: "",
      elevenLabsId: "",
      status: "inactive",
    });
    setPreviewImage(null);
    onClose();
  };

  const updateField = (
    field: keyof typeof formData,
    value: string | string[]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result as string;
        setPreviewImage(result);
        updateField("profilePic", result);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setPreviewImage(null);
    updateField("profilePic", "");
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Personification</DialogTitle>
          <DialogDescription>
            Create a new voice personification with profile picture and
            ElevenLabs integration.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Profile Picture Section */}
          <div className="space-y-4">
            <label className="text-sm font-medium">Profile Picture</label>

            {previewImage ? (
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 rounded-full overflow-hidden border-2 border-gray-200">
                  <img
                    src={previewImage}
                    alt="Profile preview"
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={removeImage}
                    className="w-fit"
                  >
                    <X className="w-4 h-4 mr-2" />
                    Remove
                  </Button>
                  <p className="text-xs text-gray-500">
                    Image uploaded successfully
                  </p>
                </div>
              </div>
            ) : (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                <p className="text-sm text-gray-600 mb-2">
                  Upload a profile picture
                </p>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                  id="profile-upload"
                />
                <label
                  htmlFor="profile-upload"
                  className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer"
                >
                  Choose File
                </label>
              </div>
            )}
          </div>

          {/* Basic Information */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Name *</label>
              <Input
                value={formData.name}
                onChange={(e) => updateField("name", e.target.value)}
                placeholder="Personification name"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium">Status</label>
              <select
                value={formData.status}
                onChange={(e) => updateField("status", e.target.value as any)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="inactive">Inactive</option>
                <option value="active">Active</option>
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
            <label className="text-sm font-medium">ElevenLabs Voice ID</label>
            <Input
              value={formData.elevenLabsId}
              onChange={(e) => updateField("elevenLabsId", e.target.value)}
              placeholder="Enter ElevenLabs voice ID (e.g., pNInz6obpgDQGcFmaJgB)"
            />
            <p className="text-xs text-gray-500 mt-1">
              Get your voice ID from the ElevenLabs dashboard
            </p>
          </div>

          <div>
            <label className="text-sm font-medium">Quotes</label>
            <Textarea
              value={formData.quotes.join("\n")}
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
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!formData.name.trim()}>
            Create Personification
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
