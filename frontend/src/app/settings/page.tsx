import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";
import { GridContainer } from "@/components/layout/GridContainer";
import { APIKeysManager } from "@/components/settings/APIKeysManager";

export const metadata = {
  title: "Settings - OpenCongress",
  description: "Manage your AI provider API keys",
};

export default async function SettingsPage() {
  const session = await auth();

  if (!session) {
    redirect("/login?callbackUrl=/settings");
  }

  return (
    <main className="min-h-screen bg-background">
      <GridContainer className="py-8">
        <h1 className="text-3xl font-bold text-foreground mb-6">Settings</h1>
        <APIKeysManager />
      </GridContainer>
    </main>
  );
}
