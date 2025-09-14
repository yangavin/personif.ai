"use client";

import { useState } from "react";
import { Button } from "@/src/components/ui/button";
import { Card } from "@/src/components/ui/card";
import { Mic, Settings, ChevronRight } from "lucide-react";
import { cn } from "@/src/lib/utils";

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const tabs = [
    {
      id: "personifications",
      label: "Personifications",
      icon: Mic,
    },
    {
      id: "settings",
      label: "Settings",
      icon: Settings,
    },
  ];

  return (
    <div className="w-64 bg-white border-r border-gray-100 h-screen flex flex-col">
      {/* Logo/Header */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center shadow-sm">
            <Mic className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-semibold text-gray-800">
            Personif.ai
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <Button
                key={tab.id}
                variant={activeTab === tab.id ? "default" : "ghost"}
                className={cn(
                  "w-full justify-start h-12 px-4 font-medium",
                  activeTab === tab.id
                    ? "bg-blue-50 text-blue-700 hover:bg-blue-100"
                    : "text-gray-600 hover:bg-gray-50"
                )}
                onClick={() => onTabChange(tab.id)}
              >
                <Icon className="w-5 h-5 mr-3" />
                {tab.label}
                {activeTab === tab.id && (
                  <ChevronRight className="w-4 h-4 ml-auto" />
                )}
              </Button>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <Card className="p-3 bg-gray-50">
          <div className="text-xs text-gray-500">
            <div className="font-medium">Voice Profiles</div>
            <div>Manage your AI personifications</div>
          </div>
        </Card>
      </div>
    </div>
  );
}
