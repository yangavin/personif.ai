"use client";

import { Card, CardContent, CardHeader } from "@/src/components/ui/card";
import { Badge } from "@/src/components/ui/badge";
import { Button } from "@/src/components/ui/button";
import { Personification } from "@/types/personification";
import { Play, Mic, Edit, Trash2 } from "lucide-react";

interface PersonificationCardProps {
  personification: Personification;
  onEdit?: (personification: Personification) => void;
  onDelete?: (personification: Personification) => void;
  isActive: boolean;
  onActivate: () => void;
}

const getProfileGradient = (id: string) => {
  const gradients = [
    "bg-gradient-to-br from-blue-200 to-blue-300",
    "bg-gradient-to-br from-green-200 to-green-300",
    "bg-gradient-to-br from-purple-200 to-purple-300",
    "bg-gradient-to-br from-orange-200 to-orange-300",
    "bg-gradient-to-br from-pink-200 to-pink-300",
    "bg-gradient-to-br from-indigo-200 to-indigo-300",
    "bg-gradient-to-br from-teal-200 to-teal-300",
    "bg-gradient-to-br from-rose-200 to-rose-300",
  ];
  return gradients[parseInt(id) % gradients.length];
};

const getActiveGlow = (id: string) => {
  const glows = [
    "shadow-blue-200 shadow-[0_0_20px_rgba(59,130,246,0.3)]",
    "shadow-green-200 shadow-[0_0_20px_rgba(34,197,94,0.3)]",
    "shadow-purple-200 shadow-[0_0_20px_rgba(168,85,247,0.3)]",
    "shadow-orange-200 shadow-[0_0_20px_rgba(249,115,22,0.3)]",
    "shadow-pink-200 shadow-[0_0_20px_rgba(236,72,153,0.3)]",
    "shadow-indigo-200 shadow-[0_0_20px_rgba(99,102,241,0.3)]",
    "shadow-teal-200 shadow-[0_0_20px_rgba(20,184,166,0.3)]",
    "shadow-rose-200 shadow-[0_0_20px_rgba(244,63,94,0.3)]",
  ];
  return glows[parseInt(id) % glows.length];
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
};

export function PersonificationCard({
  personification,
  onEdit,
  onDelete,
  isActive,
  onActivate,
}: PersonificationCardProps) {
  const profileGradient = getProfileGradient(personification.id);
  const activeGlow = getActiveGlow(personification.id);
  const initials = personification.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase();

  return (
    <Card
      className={`cursor-pointer transition-all duration-200 group border-2 border-gray-100shadow-sm w-80 h-full ${
        isActive
          ? `scale-105 shadow-xl ${activeGlow}`
          : "hover:scale-102 hover:shadow-md"
      }`}
      onClick={onActivate}
    >
      <CardHeader className="pb-6">
        <div className="flex flex-col items-center text-center space-y-4">
          <div className="relative">
            {personification.profilePic ? (
              <div className="w-20 h-20 rounded-full overflow-hidden shadow-lg">
                <img
                  src={personification.profilePic}
                  alt={personification.name}
                  className="w-full h-full object-cover"
                />
              </div>
            ) : (
              <div
                className={`w-20 h-20 ${profileGradient} rounded-full flex items-center justify-center text-white font-semibold text-2xl shadow-lg`}
              >
                {initials}
              </div>
            )}
            {isActive && (
              <div className="absolute -top-1 -right-1 w-5 h-5 bg-green-400 rounded-full flex items-center justify-center">
                <div className="w-2.5 h-2.5 bg-white rounded-full"></div>
              </div>
            )}
          </div>
          <div>
            <h3 className="font-medium text-gray-800 text-xl">
              {personification.name}
            </h3>
          </div>
          <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onEdit?.(personification);
              }}
            >
              <Edit className="w-4 h-4 mr-2" />
              Edit
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onDelete?.(personification);
              }}
              className="text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0 flex-1 flex flex-col">
        <div className="space-y-4 flex-1">
          {/* Status */}
          <div className="flex justify-center">
            <Badge
              variant="outline"
              className={`font-medium ${
                isActive
                  ? "bg-green-100 text-green-700 border-green-200"
                  : "bg-gray-100 text-gray-600 border-gray-200"
              }`}
            >
              {isActive ? "Active" : personification.status}
            </Badge>
          </div>

          {/* Content preview */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-100 flex-1">
            <p
              className="text-sm text-gray-600 font-normal text-center line-clamp-4"
              title={personification.content}
            >
              {personification.content.length > 200
                ? `${personification.content.substring(0, 200)}...`
                : personification.content}
            </p>
          </div>

          {/* Quotes preview */}
          {personification.quotes && personification.quotes.length > 0 && (
            <div className="bg-blue-50 rounded-lg p-3 border border-blue-100">
              <h4 className="text-xs font-medium text-blue-800 mb-2">Quotes</h4>
              <div className="space-y-1">
                {personification.quotes.slice(0, 2).map((quote, index) => (
                  <p
                    key={index}
                    className="text-xs text-blue-700 italic line-clamp-2"
                    title={quote}
                  >
                    "
                    {quote.length > 80 ? `${quote.substring(0, 80)}...` : quote}
                    "
                  </p>
                ))}
                {personification.quotes.length > 2 && (
                  <p className="text-xs text-blue-600 font-medium">
                    +{personification.quotes.length - 2} more quotes
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Last Updated */}
          <div className="text-center">
            <div className="text-xs text-gray-500 font-normal">
              {formatDate(personification.updatedAt)}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
