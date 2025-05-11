"use client";

import { LoggedEvent } from "@/app/types";
import {
  createContext,
  FC,
  PropsWithChildren,
  useContext,
  useState,
} from "react";
import { v4 as uuidv4 } from "uuid";

type EventContextValue = {
  loggedEvents: LoggedEvent[];
  logClientEvent: (
    eventObj: Record<string, any>,
    eventNameSuffix?: string
  ) => void;
  logServerEvent: (
    eventObj: Record<string, any>,
    eventNameSuffix?: string
  ) => void;
  logFunctionCall: (functionName: string, args: any, result?: any) => void;
  toggleExpand: (id: number | string) => void;
};

const EventContext = createContext<EventContextValue | undefined>(undefined);

export const EventProvider: FC<PropsWithChildren> = ({ children }) => {
  const [loggedEvents, setLoggedEvents] = useState<LoggedEvent[]>([]);

  function addLoggedEvent(
    direction: "client" | "server",
    eventName: string,
    eventData: Record<string, any>
  ) {
    const id = eventData.event_id || uuidv4();
    setLoggedEvents((prev) => [
      ...prev,
      {
        id,
        direction,
        eventName,
        eventData,
        timestamp: new Date().toLocaleTimeString(),
        expanded: false,
        type: eventData.type || "general",
      },
    ]);
  }

  const logClientEvent: EventContextValue["logClientEvent"] = (
    eventObj,
    eventNameSuffix = ""
  ) => {
    const name = `${eventObj.type || ""} ${eventNameSuffix || ""}`.trim();
    addLoggedEvent("client", name, eventObj);
  };

  const logServerEvent: EventContextValue["logServerEvent"] = (
    eventObj,
    eventNameSuffix = ""
  ) => {
    const name = `${eventObj.type || ""} ${eventNameSuffix || ""}`.trim();
    addLoggedEvent("server", name, eventObj);
  };

  const logFunctionCall: EventContextValue["logFunctionCall"] = (
    functionName,
    args,
    result
  ) => {
    const eventData = {
      type: "function_call",
      function: functionName,
      arguments: args,
      result: result,
      timestamp: new Date().toISOString(),
    };

    const eventName = result
      ? `Function Result: ${functionName}`
      : `Function Call: ${functionName}`;
    addLoggedEvent("client", eventName, eventData);

    // Auto-expand function calls with errors
    if (result && result.error) {
      const id = uuidv4();
      setLoggedEvents((prev) =>
        prev.map((log) =>
          log.timestamp === id ? { ...log, expanded: true } : log
        )
      );
    }
  };

  const toggleExpand: EventContextValue["toggleExpand"] = (id) => {
    setLoggedEvents((prev) =>
      prev.map((log) => {
        if (log.id === id) {
          return { ...log, expanded: !log.expanded };
        }
        return log;
      })
    );
  };

  return (
    <EventContext.Provider
      value={{
        loggedEvents,
        logClientEvent,
        logServerEvent,
        logFunctionCall,
        toggleExpand,
      }}
    >
      {children}
    </EventContext.Provider>
  );
};

export function useEvent() {
  const context = useContext(EventContext);
  if (!context) {
    throw new Error("useEvent must be used within an EventProvider");
  }
  return context;
}
