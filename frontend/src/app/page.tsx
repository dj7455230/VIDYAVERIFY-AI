"use client";

import { AppShell } from "@/components/AppShell";
import { Dashboard } from "@/features/dashboard/Dashboard";

export default function Home() {
  return (
    <AppShell>
      <Dashboard />
    </AppShell>
  );
}
