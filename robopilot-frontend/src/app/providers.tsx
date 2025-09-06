"use client";

import React, { useEffect } from "react";
import { AudioProvider } from "@/app/contexts/AudioContext";
import { LMStudioProvider } from "@/app/contexts/LMStudioContext";
import initializeAudio from "@/app/utils/audioInit";

export const ClientProviders = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  useEffect(() => {
    // Initialize audio subsystems when the app starts
    initializeAudio().then((success) => {
      if (success) {
        console.log("Audio systems initialized successfully");
      } else {
        console.warn(
          "Audio initialization failed, some features may not work correctly"
        );
      }
    });
  }, []);

  return (
    <LMStudioProvider>
      <AudioProvider>{children}</AudioProvider>
    </LMStudioProvider>
  );
};
