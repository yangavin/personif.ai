"use client";

import React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/src/components/ui/dialog";
import { Button } from "@/src/components/ui/button";
import { Personification } from "@/types/personification";
import { AlertTriangle, Trash2 } from "lucide-react";

interface DeleteConfirmationDialogProps {
  personification: Personification | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (personification: Personification) => void;
}

export function DeleteConfirmationDialog({
  personification,
  isOpen,
  onClose,
  onConfirm,
}: DeleteConfirmationDialogProps) {
  if (!personification) return null;

  const handleConfirm = () => {
    onConfirm(personification);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <DialogTitle>Delete Personification</DialogTitle>
              <DialogDescription>
                This action cannot be undone.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-3">
              {personification.profilePic ? (
                <div className="w-12 h-12 rounded-full overflow-hidden">
                  <img
                    src={personification.profilePic}
                    alt={personification.name}
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : (
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-semibold text-lg">
                    {personification.name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")
                      .toUpperCase()}
                  </span>
                </div>
              )}
              <div>
                <h3 className="font-medium text-gray-900">
                  {personification.name}
                </h3>
                <p className="text-sm text-gray-600">
                  {personification.description}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-medium text-red-900 mb-1">Warning</h4>
                <p className="text-sm text-red-700">
                  You are about to permanently delete "{personification.name}".
                  This will remove all associated data including voice settings,
                  prompts, and configuration. This action cannot be undone.
                </p>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleConfirm}
            className="bg-red-600 hover:bg-red-700"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Delete Personification
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
