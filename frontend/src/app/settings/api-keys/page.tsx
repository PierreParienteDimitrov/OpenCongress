import { APIKeysManager } from "@/components/settings/APIKeysManager";

export const metadata = {
  title: "API Keys - Settings - OpenCongress",
  description: "Manage your AI provider API keys",
};

export default function APIKeysPage() {
  return <APIKeysManager />;
}
