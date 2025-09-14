"use client";

import { useState, useEffect } from "react";
import { PersonificationCard } from "@/src/components/personification-card";
import { EditPersonificationDialog } from "@/src/components/edit-personification-dialog";
import { NewPersonificationDialog } from "@/src/components/new-personification-dialog";
import { DeleteConfirmationDialog } from "@/src/components/delete-confirmation-dialog";
import { Button } from "@/src/components/ui/button";
import { getPersonifications, setActivePersonification } from "@/src/lib/api";
import { Personification } from "@/types/personification";
import { Plus, Filter } from "lucide-react";

interface PersonificationsPageProps {
  onTabChange: (tab: string) => void;
}

export function PersonificationsPage({
  onTabChange,
}: PersonificationsPageProps) {
  const [personifications, setPersonifications] = useState<Personification[]>(
    []
  );
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load personifications on component mount
  useEffect(() => {
    loadPersonifications();
  }, []);

  const loadPersonifications = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getPersonifications();
      setPersonifications(data.personifications);
      setActivePersonificationId(data.activeChoice);
    } catch (err) {
      console.error("Error loading personifications:", err);
      setError("Failed to load personifications");
    } finally {
      setLoading(false);
    }
  };

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

  const handleActivatePersonification = async (personificationId: string) => {
    try {
      const newActiveId =
        activePersonificationId === personificationId
          ? null
          : personificationId;

      // Optimistically update the UI
      setActivePersonificationId(newActiveId);

      // Update on server
      await setActivePersonification(newActiveId);
    } catch (err) {
      console.error("Error updating active personification:", err);
      // Revert the optimistic update on error
      setActivePersonificationId(activePersonificationId);
      setError("Failed to update active personification");
    }
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
          {loading ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-gray-500">Loading personifications...</div>
            </div>
          ) : error ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="text-red-600 mb-2">{error}</div>
                <Button
                  onClick={loadPersonifications}
                  variant="outline"
                  size="sm"
                >
                  Try Again
                </Button>
              </div>
            </div>
          ) : personifications.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="text-gray-500 mb-4">
                  No personifications found
                </div>
                <Button onClick={() => setIsNewDialogOpen(true)} size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Your First Personification
                </Button>
              </div>
            </div>
          ) : (
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
          )}
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
