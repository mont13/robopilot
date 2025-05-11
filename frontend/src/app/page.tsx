"use client";

import { EventProvider } from "@/app/contexts/EventContext";
import { TranscriptProvider } from "@/app/contexts/TranscriptContext";
import dynamic from "next/dynamic";

// Dynamically import components with client-side only rendering and no SSR
const DynamicApp = dynamic(() => import("./App"), { ssr: false });
const DynamicProviders = dynamic(
  () => import("./providers").then((mod) => mod.ClientProviders),
  { ssr: false },
);

export default function Page() {
  return (
    <TranscriptProvider>
      <EventProvider>
        <DynamicProviders>
          <DynamicApp />
        </DynamicProviders>
      </EventProvider>
    </TranscriptProvider>
  );
}
