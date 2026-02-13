"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useWorkspace } from "@/lib/hooks/useWorkspace";
import { useUIStore } from "@/lib/stores/uiStore";
import { useAuthStore } from "@/lib/stores/authStore";
import { toast } from "@/lib/hooks/useToast";

export default function SettingsPage() {
  const activeWorkspaceId = useUIStore((s) => s.activeWorkspaceId);
  const { data: workspace, isLoading } = useWorkspace(activeWorkspaceId);
  const user = useAuthStore((s) => s.user);

  const [displayName, setDisplayName] = useState(user?.name ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Manage your workspace and account settings.
        </p>
      </div>

      {/* Workspace Settings */}
      {workspace && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Workspace</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-sm">Name</Label>
              <Input
                value={workspace.name}
                disabled
                className="mt-1"
              />
            </div>
            <div>
              <Label className="text-sm">Slug</Label>
              <Input
                value={workspace.slug}
                disabled
                className="mt-1"
              />
            </div>
            <div>
              <Label className="text-sm">Your Role</Label>
              <Input
                value={workspace.role.charAt(0).toUpperCase() + workspace.role.slice(1)}
                disabled
                className="mt-1"
              />
            </div>
          </CardContent>
        </Card>
      )}

      <Separator />

      {/* User Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-sm">Email</Label>
            <Input
              value={user?.email ?? ""}
              disabled
              className="mt-1"
            />
          </div>
          <div>
            <Label className="text-sm">Display Name</Label>
            <Input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Your name"
              className="mt-1"
            />
          </div>
          <Button
            size="sm"
            onClick={() => {
              toast({
                title: "Coming soon",
                description: "Profile updates will be available in a future release.",
              });
            }}
          >
            Update Profile
          </Button>
        </CardContent>
      </Card>

      <Separator />

      {/* Password Change */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Change Password</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-sm">Current Password</Label>
            <Input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="mt-1"
            />
          </div>
          <div>
            <Label className="text-sm">New Password</Label>
            <Input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="mt-1"
            />
          </div>
          <Button
            size="sm"
            onClick={() => {
              toast({
                title: "Coming soon",
                description: "Password changes will be available in a future release.",
              });
            }}
          >
            Change Password
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
