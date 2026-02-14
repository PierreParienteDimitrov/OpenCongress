import Link from "next/link";

import { GridContainer } from "@/components/layout/GridContainer";
import { routes } from "@/lib/routes";
import {
  DocSection,
  DocSidebar,
  InfoCard,
  SourceBadge,
} from "./components";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export const metadata = {
  title: "How OpenCongress Works - Documentation",
  description:
    "Learn about our data sources, update processes, and technology that powers OpenCongress",
  alternates: { canonical: "/documentation" },
  openGraph: {
    title: "How OpenCongress Works - Documentation",
    description:
      "Learn about our data sources, update processes, and technology that powers OpenCongress.",
    url: "/documentation",
  },
  twitter: {
    card: "summary" as const,
    title: "How OpenCongress Works",
    description:
      "Learn about our data sources, update processes, and technology that powers OpenCongress.",
  },
};

const sections = [
  { id: "overview", label: "Overview" },
  { id: "data-sources", label: "Data Sources" },
  { id: "data-updates", label: "How Data is Updated" },
  { id: "ai-content", label: "AI-Generated Content" },
  { id: "api-keys", label: "API Keys Setup" },
  { id: "technology", label: "Technology" },
  { id: "open-source", label: "Open Source" },
];

function OverviewIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

function DataSourceIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
      />
    </svg>
  );
}

function UpdateIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
      />
    </svg>
  );
}

function AIIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
      />
    </svg>
  );
}

function APIKeyIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
      />
    </svg>
  );
}

function TechIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
      />
    </svg>
  );
}

function OpenSourceIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
      />
    </svg>
  );
}

export default function DocumentationPage() {
  return (
    <main className="min-h-screen bg-background">
      <GridContainer className="py-8">
        {/* Header */}
        <header className="mb-8">
          <Link
            href={routes.home}
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-4"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Home
          </Link>
          <h1 className="text-3xl font-bold text-foreground mb-2">
            How OpenCongress Works
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Transparency is at the heart of what we do. Learn about our data sources,
            how we keep information up to date, and the technology that powers this platform.
          </p>
        </header>

        {/* Two-column layout */}
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Left Sidebar - sticky on desktop */}
          <aside className="lg:w-64 flex-shrink-0">
            <div className="lg:sticky lg:top-8">
              <DocSidebar sections={sections} />
            </div>
          </aside>

          {/* Main Content */}
          <article className="flex-1 min-w-0 space-y-6">
            {/* Overview Section */}
            <DocSection id="overview" title="Overview" icon={<OverviewIcon />}>
              <p>
                OpenCongress is a free, nonpartisan platform designed to make congressional
                information accessible to everyone. We believe that understanding what happens
                in Congress shouldn&apos;t require specialized knowledge or expensive subscriptions.
              </p>
              <p>
                Our mission is simple: provide clear, accurate, and timely information about
                congressional activity, from roll-call votes to legislation, without editorial
                bias or political spin.
              </p>
              <div className="grid gap-4 sm:grid-cols-3 mt-4">
                <div className="bg-secondary rounded-lg p-4">
                  <div className="text-2xl font-bold text-foreground">100%</div>
                  <div className="text-sm text-muted-foreground">Free to use</div>
                </div>
                <div className="bg-secondary rounded-lg p-4">
                  <div className="text-2xl font-bold text-foreground">Nonpartisan</div>
                  <div className="text-sm text-muted-foreground">Fact-based info</div>
                </div>
                <div className="bg-secondary rounded-lg p-4">
                  <div className="text-2xl font-bold text-foreground">Open</div>
                  <div className="text-sm text-muted-foreground">Source available</div>
                </div>
              </div>
            </DocSection>

            {/* Data Sources Section */}
            <DocSection id="data-sources" title="Data Sources" icon={<DataSourceIcon />}>
              <p>
                All congressional data on OpenCongress comes directly from official government sources.
                We don&apos;t filter, editorialize, or modify the data in any way.
              </p>

              <div className="bg-secondary rounded-lg p-4 mt-4">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-card rounded-lg shadow-sm">
                    <svg className="w-6 h-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-foreground">Congress.gov API</h3>
                      <SourceBadge name="Official Source" official />
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Operated by the Library of Congress, this is the authoritative source for all
                      congressional data including votes, legislation, and member information.
                    </p>
                    <a
                      href="https://api.congress.gov/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-sm text-accent hover:underline mt-2"
                    >
                      Learn more about the API
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </div>
                </div>
              </div>

              <h3 className="font-semibold text-foreground mt-6 mb-3">What we track:</h3>
              <ul className="space-y-2">
                <li className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span><strong>Roll-call votes</strong> — Every recorded vote in the House and Senate</span>
                </li>
                <li className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span><strong>Legislation</strong> — Bills, resolutions, and their full text</span>
                </li>
                <li className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span><strong>Member information</strong> — Profiles and committee assignments</span>
                </li>
              </ul>

              <InfoCard type="success" title="Verification">
                Every piece of data includes direct links to the official Congress.gov page so you
                can always verify the information at its source.
              </InfoCard>
            </DocSection>

            {/* Data Updates Section */}
            <DocSection id="data-updates" title="How Data is Updated" icon={<UpdateIcon />}>
              <p>
                We sync data from Congress.gov on a regular schedule to ensure you have access
                to the latest information. Different types of data are updated at different
                frequencies based on how often they change.
              </p>

              <div className="overflow-x-auto mt-4">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Data Type</TableHead>
                      <TableHead>Update Frequency</TableHead>
                      <TableHead>Notes</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell className="font-medium">Votes</TableCell>
                      <TableCell>Hourly during session</TableCell>
                      <TableCell className="text-muted-foreground">9am–9pm ET on weekdays</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Bills</TableCell>
                      <TableCell>Daily</TableCell>
                      <TableCell className="text-muted-foreground">Every morning</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Members</TableCell>
                      <TableCell>Weekly</TableCell>
                      <TableCell className="text-muted-foreground">Sunday sync</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>

              <InfoCard type="info">
                Real-time availability depends on the Congress.gov API. There may be occasional
                delays between when Congress takes action and when it appears on our platform.
              </InfoCard>
            </DocSection>

            {/* AI Content Section */}
            <DocSection id="ai-content" title="AI-Generated Content" icon={<AIIcon />}>
              <p>
                We use AI to help make congressional information more accessible. All AI-generated
                content is clearly labeled so you always know what you&apos;re reading.
              </p>

              <h3 className="font-semibold text-foreground mt-6 mb-3">What&apos;s AI-generated:</h3>
              <ul className="space-y-2">
                <li className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-purple-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <span><strong>Bill summaries</strong> — Plain-English explanations of what legislation does</span>
                </li>
                <li className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-purple-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <span><strong>Weekly summaries</strong> — Recap and preview of congressional activity</span>
                </li>
                <li className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-purple-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <span><strong>Member bios</strong> — Brief biographical information</span>
                </li>
              </ul>

              <div className="bg-purple-50 rounded-lg p-4 mt-4 dark:bg-purple-900/20">
                <h4 className="font-semibold text-purple-900 mb-2 dark:text-purple-300">Our AI Principles</h4>
                <ul className="space-y-2 text-sm text-purple-800 dark:text-purple-300/80">
                  <li className="flex items-start gap-2">
                    <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span><strong>Clearly labeled</strong> — AI content is always marked</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span><strong>Nonpartisan</strong> — Written to be factual, not persuasive</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span><strong>Source available</strong> — Original text always accessible</span>
                  </li>
                </ul>
              </div>

              <p className="text-sm text-muted-foreground mt-4">
                AI summaries are generated using Google&apos;s Gemini 2.5 Flash model, chosen for its
                speed and accuracy with factual content.
              </p>
            </DocSection>

            {/* API Keys Setup Section */}
            <DocSection id="api-keys" title="API Keys Setup" icon={<APIKeyIcon />}>
              <p>
                OpenCongress includes an AI assistant that can answer questions about Congress
                using your own API key. You need a key from at least one provider to use it.
                Keys are encrypted at rest and never shared.
              </p>

              <InfoCard type="info" title="Where to add your key">
                Once you have a key, go to{" "}
                <Link href={routes.settings.apiKeys} className="font-medium underline underline-offset-2">
                  Settings &rarr; API Keys
                </Link>{" "}
                to save it to your account.
              </InfoCard>

              {/* Anthropic */}
              <div className="rounded-lg border p-4 mt-4">
                <div className="flex items-center gap-2 mb-3">
                  <h3 className="font-semibold text-foreground">Anthropic (Claude)</h3>
                  <Badge variant="secondary" className="text-xs">Recommended</Badge>
                </div>
                <ol className="list-decimal list-inside space-y-2 text-sm">
                  <li>
                    Go to the{" "}
                    <a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">
                      Anthropic Console
                    </a>
                  </li>
                  <li>Sign up or log in to your account</li>
                  <li>Navigate to <strong>Settings &rarr; API Keys</strong></li>
                  <li>Click <strong>Create Key</strong>, give it a name, and copy the key</li>
                  <li>Paste the key in your OpenCongress settings (starts with <code className="bg-secondary px-1.5 py-0.5 rounded text-xs">sk-ant-</code>)</li>
                </ol>
              </div>

              {/* OpenAI */}
              <div className="rounded-lg border p-4 mt-2">
                <h3 className="font-semibold text-foreground mb-3">OpenAI (GPT)</h3>
                <ol className="list-decimal list-inside space-y-2 text-sm">
                  <li>
                    Go to the{" "}
                    <a href="https://platform.openai.com/" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">
                      OpenAI Platform
                    </a>
                  </li>
                  <li>Sign up or log in to your account</li>
                  <li>Navigate to <strong>API Keys</strong> in the left sidebar</li>
                  <li>Click <strong>Create new secret key</strong>, name it, and copy the key</li>
                  <li>Paste the key in your OpenCongress settings (starts with <code className="bg-secondary px-1.5 py-0.5 rounded text-xs">sk-</code>)</li>
                </ol>
              </div>

              {/* Google */}
              <div className="rounded-lg border p-4 mt-2">
                <h3 className="font-semibold text-foreground mb-3">Google (Gemini)</h3>
                <ol className="list-decimal list-inside space-y-2 text-sm">
                  <li>
                    Go to{" "}
                    <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">
                      Google AI Studio
                    </a>
                  </li>
                  <li>Sign in with your Google account</li>
                  <li>Click <strong>Create API Key</strong></li>
                  <li>Select a Google Cloud project (or create one)</li>
                  <li>Copy the generated key and paste it in your OpenCongress settings (starts with <code className="bg-secondary px-1.5 py-0.5 rounded text-xs">AIza</code>)</li>
                </ol>
                <p className="text-xs text-muted-foreground mt-2">
                  Google offers a generous free tier for Gemini API usage.
                </p>
              </div>

              <InfoCard type="warning" title="Keep your keys safe">
                API keys are like passwords — never share them publicly. Each provider
                lets you revoke and regenerate keys at any time from their dashboard.
              </InfoCard>
            </DocSection>

            {/* Technology Section */}
            <DocSection id="technology" title="Technology" icon={<TechIcon />}>
              <p>
                OpenCongress is built with modern, reliable technology to ensure a fast and
                accessible experience on any device.
              </p>

              <div className="grid gap-4 sm:grid-cols-2 mt-4">
                <div className="bg-secondary rounded-lg p-4">
                  <h4 className="font-semibold text-foreground mb-1">Fast & Responsive</h4>
                  <p className="text-sm text-muted-foreground">
                    Built for speed with server-side rendering and optimized data loading
                  </p>
                </div>
                <div className="bg-secondary rounded-lg p-4">
                  <h4 className="font-semibold text-foreground mb-1">Works Everywhere</h4>
                  <p className="text-sm text-muted-foreground">
                    Designed to work on phones, tablets, and desktops
                  </p>
                </div>
                <div className="bg-secondary rounded-lg p-4">
                  <h4 className="font-semibold text-foreground mb-1">Secure</h4>
                  <p className="text-sm text-muted-foreground">
                    All connections encrypted, no tracking or data collection
                  </p>
                </div>
                <div className="bg-secondary rounded-lg p-4">
                  <h4 className="font-semibold text-foreground mb-1">Accessible</h4>
                  <p className="text-sm text-muted-foreground">
                    Built with accessibility in mind, including screen reader support
                  </p>
                </div>
              </div>
            </DocSection>

            {/* Open Source Section */}
            <DocSection id="open-source" title="Open Source" icon={<OpenSourceIcon />}>
              <p>
                OpenCongress is open source software. We believe transparency in civic technology
                starts with transparent code.
              </p>

              <div className="bg-primary rounded-lg p-6 mt-4 text-primary-foreground">
                <div className="flex items-center gap-3 mb-3">
                  <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                  <div>
                    <h4 className="font-semibold">View on GitHub</h4>
                    <p className="text-sm text-muted-foreground/60">Explore the code, report issues, or contribute</p>
                  </div>
                </div>
                <Button variant="secondary" asChild>
                  <a
                    href="https://github.com/OpenCongress"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Visit Repository
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </Button>
              </div>

              <h3 className="font-semibold text-foreground mt-6 mb-3">Ways to Contribute</h3>
              <ul className="space-y-2">
                <li className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-accent mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span><strong>Report bugs</strong> — Found something broken? Let us know</span>
                </li>
                <li className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-accent mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <span><strong>Suggest features</strong> — Have an idea? We&apos;d love to hear it</span>
                </li>
                <li className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-accent mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                  <span><strong>Contribute code</strong> — Pull requests are welcome</span>
                </li>
              </ul>
            </DocSection>
          </article>
        </div>
      </GridContainer>
    </main>
  );
}
