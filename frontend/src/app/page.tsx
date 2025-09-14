"use client";

import { useState } from "react";
import { Sidebar } from "@/src/components/sidebar";
import { SettingsPage } from "@/src/pages/settings-page";
import { PersonificationsPage } from "@/src/pages/personifications-page";

export default function Home() {
  const [activeTab, setActiveTab] = useState("personifications");

  return (
    <div className="min-h-screen bg-white flex">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <div className="flex-1 overflow-auto">
        {activeTab === "personifications" && (
          <PersonificationsPage onTabChange={setActiveTab} />
        )}
        {activeTab === "settings" && <SettingsPage />}
      </div>
    </div>
  );
}
