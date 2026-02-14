import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";
import { GridContainer } from "@/components/layout/GridContainer";
import { SettingsNav } from "@/components/settings/SettingsNav";

export const metadata = {
  title: "Settings - OpenCongress",
  description: "Manage your account settings",
};

export default async function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();

  if (!session) {
    redirect("/login?callbackUrl=/settings");
  }

  return (
    <main className="min-h-screen bg-background">
      <GridContainer className="py-8">
        <h1 className="text-3xl font-bold text-foreground mb-6">Settings</h1>
        <div className="grid gap-6 md:grid-cols-[200px_1fr]">
          <SettingsNav />
          <div>{children}</div>
        </div>
      </GridContainer>
    </main>
  );
}
