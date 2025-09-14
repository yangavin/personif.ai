"use client";

import { useState } from "react";
import { PersonificationCard } from "@/src/components/personification-card";
import { EditPersonificationDialog } from "@/src/components/edit-personification-dialog";
import { NewPersonificationDialog } from "@/src/components/new-personification-dialog";
import { DeleteConfirmationDialog } from "@/src/components/delete-confirmation-dialog";
import { Button } from "@/src/components/ui/button";
import { mockPersonifications } from "@/src/lib/mock-data";
import { Personification } from "@/types/personification";
import { Plus, Filter } from "lucide-react";

interface PersonificationsPageProps {
  onTabChange: (tab: string) => void;
}

export function PersonificationsPage({
  onTabChange,
}: PersonificationsPageProps) {
  const [personifications, setPersonifications] =
    useState(mockPersonifications);
  const [editingPersonification, setEditingPersonification] =
    useState<Personification | null>(null);
  const [deletingPersonification, setDeletingPersonification] =
    useState<Personification | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isNewDialogOpen, setIsNewDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [activePersonificationId, setActivePersonificationId] = useState<
    string | null
  >(null);

  const handleEditPersonification = (personification: Personification) => {
    setEditingPersonification(personification);
    setIsEditDialogOpen(true);
  };

  const handleSavePersonification = (
    updatedPersonification: Personification
  ) => {
    setPersonifications((prev) =>
      prev.map((p) =>
        p.id === updatedPersonification.id ? updatedPersonification : p
      )
    );
  };

  const handleCreatePersonification = (
    newPersonification: Omit<Personification, "id" | "createdAt" | "updatedAt">
  ) => {
    const personification: Personification = {
      ...newPersonification,
      id: Date.now().toString(), // Simple ID generation
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    setPersonifications((prev) => [...prev, personification]);
  };

  const handleDeletePersonification = (personification: Personification) => {
    setDeletingPersonification(personification);
    setIsDeleteDialogOpen(true);
  };

  const handleConfirmDelete = (personification: Personification) => {
    setPersonifications((prev) =>
      prev.filter((p) => p.id !== personification.id)
    );

    // If the deleted personification was active, clear the active state
    if (activePersonificationId === personification.id) {
      setActivePersonificationId(null);
    }
  };

  const handleActivatePersonification = (personificationId: string) => {
    setActivePersonificationId(
      activePersonificationId === personificationId ? null : personificationId
    );
  };

  return (
    <>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <div className="flex-shrink-0 p-6 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-800">
                Personifications
              </h1>
              <p className="text-sm text-gray-600 mt-1 font-normal">
                Manage your voice profiles and transcripts
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-sm text-blue-600 font-medium bg-blue-50 px-3 py-1 rounded-full">
                {personifications.length} personifications
              </div>
              <Button variant="outline" size="sm">
                <Filter className="w-4 h-4 mr-2" />
                Filter
              </Button>
              <Button size="sm" onClick={() => setIsNewDialogOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                New Personification
              </Button>
            </div>
          </div>
        </div>

        {/* Horizontal Scroll Container */}
        <div className="flex-1 overflow-x-auto overflow-y-hidden">
          <div className="h-full flex items-center px-6 py-6 gap-6 min-w-max">
            {personifications.map((personification) => (
              <div key={personification.id} className="flex-shrink-0 h-full">
                <PersonificationCard
                  personification={personification}
                  onEdit={handleEditPersonification}
                  onDelete={handleDeletePersonification}
                  isActive={activePersonificationId === personification.id}
                  onActivate={() =>
                    handleActivatePersonification(personification.id)
                  }
                />
              </div>
            ))}
          </div>
        </div>
      </div>

      <EditPersonificationDialog
        personification={editingPersonification}
        isOpen={isEditDialogOpen}
        onClose={() => {
          setIsEditDialogOpen(false);
          setEditingPersonification(null);
        }}
        onSave={handleSavePersonification}
      />

      <NewPersonificationDialog
        isOpen={isNewDialogOpen}
        onClose={() => setIsNewDialogOpen(false)}
        onSave={handleCreatePersonification}
      />

      <DeleteConfirmationDialog
        personification={deletingPersonification}
        isOpen={isDeleteDialogOpen}
        onClose={() => {
          setIsDeleteDialogOpen(false);
          setDeletingPersonification(null);
        }}
        onConfirm={handleConfirmDelete}
      />
    </>
  );
}
