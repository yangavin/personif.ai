"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/src/components/ui/card";
import { Button } from "@/src/components/ui/button";
import { Badge } from "@/src/components/ui/badge";
import { Settings, Mic, Volume2, Shield, Database, Bell } from "lucide-react";

export function SettingsPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-800">Settings</h1>
        <p className="text-sm text-gray-600 mt-1 font-normal">
          Configure your voice recognition and application preferences
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Voice Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-800">
              <Mic className="w-5 h-5 text-blue-600" />
              Voice Recognition
            </CardTitle>
            <CardDescription className="text-gray-600">
              Configure voice profile settings and recognition parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-800">
                  Similarity Threshold
                </div>
                <div className="text-sm text-gray-600">0.7 (Recommended)</div>
              </div>
              <Badge
                variant="outline"
                className="bg-blue-50 text-blue-700 border-blue-200"
              >
                Active
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-800">Auto-enrollment</div>
                <div className="text-sm text- v">
                  Automatically enroll new voices
                </div>
              </div>
              <Badge
                variant="outline"
                className="bg-green-50 text-green-700 border-green-200"
              >
                Enabled
              </Badge>
            </div>

            <Button className="w-full bg-white border border-gray-200 hover:bg-gray-200 text-gray-800">
              Configure Voice Settings
            </Button>
          </CardContent>
        </Card>

        {/* Audio Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-800">
              <Volume2 className="w-5 h-5 text-purple-600" />
              Audio Processing
            </CardTitle>
            <CardDescription className="text-gray-600">
              Adjust audio quality and processing parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-800">Sample Rate</div>
                <div className="text-sm text-gray-600">16kHz (Optimal)</div>
              </div>
              <Badge
                variant="outline"
                className="bg-purple-50 text-purple-700 border-purple-200"
              >
                16kHz
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-800">Chunk Duration</div>
                <div className="text-sm text-gray-600">3 seconds</div>
              </div>
              <Badge
                variant="outline"
                className="bg-purple-50 text-purple-700 border-purple-200"
              >
                3s
              </Badge>
            </div>

            <Button className="w-full bg-white border border-gray-200 hover:bg-gray-200 text-gray-800">
              Adjust Audio Settings
            </Button>
          </CardContent>
        </Card>

        {/* Security Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-800">
              <Shield className="w-5 h-5 text-green-600" />
              Security & Privacy
            </CardTitle>
            <CardDescription className="text-gray-600">
              Manage data privacy and security preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-800">Data Encryption</div>
                <div className="text-sm text-gray-600">
                  Voice profiles are encrypted
                </div>
              </div>
              <Badge
                variant="outline"
                className="bg-green-50 text-green-700 border-green-200"
              >
                Enabled
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-800">Auto-delete</div>
                <div className="text-sm text-gray-600">
                  Delete old transcripts after 30 days
                </div>
              </div>
              <Badge
                variant="outline"
                className="bg-green-50 text-green-700 border-green-200"
              >
                Enabled
              </Badge>
            </div>

            <Button className="w-full bg-white border border-gray-200 hover:bg-gray-200 text-gray-800">
              Privacy Settings
            </Button>
          </CardContent>
        </Card>

        {/* System Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-800">
              <Database className="w-5 h-5 text-orange-600" />
              System & Storage
            </CardTitle>
            <CardDescription className="text-gray-600">
              Monitor system resources and storage usage
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-800">Storage Used</div>
                <div className="text-sm text-gray-600">2.3 GB of 10 GB</div>
              </div>
              <Badge
                variant="outline"
                className="bg-orange-50 text-orange-700 border-orange-200"
              >
                23%
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-800">Model Status</div>
                <div className="text-sm text-gray-600">SpeechBrain v0.5.16</div>
              </div>
              <Badge
                variant="outline"
                className="bg-green-50 text-green-700 border-green-200"
              >
                Ready
              </Badge>
            </div>

            <Button className="w-full bg-white border border-gray-200 hover:bg-gray-200 text-gray-800">
              System Information
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Notifications */}
    </div>
  );
}
