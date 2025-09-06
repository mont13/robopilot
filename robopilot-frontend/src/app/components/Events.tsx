"use client";

import { useEvent } from "@/app/contexts/EventContext";
import { LoggedEvent } from "@/app/types";
import { useEffect, useRef, useState } from "react";

export interface EventsProps {
  isExpanded: boolean;
  defaultExpanded?: boolean; // Automatically expand certain log types
}

function Events({ isExpanded }: EventsProps) {
  const [prevEventLogs, setPrevEventLogs] = useState<LoggedEvent[]>([]);
  const eventLogsContainerRef = useRef<HTMLDivElement | null>(null);

  const { loggedEvents, toggleExpand } = useEvent();

  const getDirectionArrow = (direction: string) => {
    if (direction === "client") return { symbol: "▲", color: "#7f5af0" };
    if (direction === "server") return { symbol: "▼", color: "#2cb67d" };
    return { symbol: "•", color: "#555" };
  };

  useEffect(() => {
    const hasNewEvent = loggedEvents.length > prevEventLogs.length;

    if (isExpanded && hasNewEvent && eventLogsContainerRef.current) {
      eventLogsContainerRef.current.scrollTop =
        eventLogsContainerRef.current.scrollHeight;
    }

    setPrevEventLogs(loggedEvents);
  }, [loggedEvents, isExpanded]);

  const getEventBadgeStyles = (log: LoggedEvent) => {
    // Function call specific styling
    if (log.eventData.type === "function_call") {
      const isResult = log.eventName.startsWith("Function Result");
      const hasError = log.eventData.result?.error;

      if (hasError) {
        return "bg-red-100 border-red-300 text-red-800";
      } else if (isResult) {
        return "bg-green-100 border-green-300 text-green-800";
      } else {
        return "bg-blue-100 border-blue-300 text-blue-800";
      }
    }

    // Default styling
    const isError =
      log.eventName.toLowerCase().includes("error") ||
      log.eventData?.response?.status_details?.error != null;

    return isError ? "bg-red-50 border-red-100" : "";
  };

  const renderFunctionCallDetails = (log: LoggedEvent) => {
    if (log.eventData.type !== "function_call") return null;

    const { function: fnName, arguments: args, result } = log.eventData;

    return (
      <div className="mt-2">
        {!log.eventName.startsWith("Function Result") && (
          <div className="mb-2">
            <span className="font-semibold">Function: </span>
            <span className="text-blue-600">{fnName}</span>
          </div>
        )}

        {!log.eventName.startsWith("Function Result") && args && (
          <div className="mb-2">
            <div className="font-semibold">Arguments:</div>
            <pre className="border-l-2 border-blue-200 whitespace-pre-wrap break-words pl-2 mt-1 text-xs">
              {JSON.stringify(args, null, 2)}
            </pre>
          </div>
        )}

        {result && (
          <div>
            <div className="font-semibold">Result:</div>
            <pre
              className={`border-l-2 ${result.error ? "border-red-300" : "border-green-300"} whitespace-pre-wrap break-words pl-2 mt-1 text-xs`}
            >
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      className={
        (isExpanded ? "w-1/2 overflow-auto" : "w-0 overflow-hidden opacity-0") +
        " transition-all rounded-xl duration-200 ease-in-out flex flex-col bg-white"
      }
      ref={eventLogsContainerRef}
    >
      {isExpanded && (
        <div>
          <div className="font-semibold px-6 py-4 sticky top-0 z-10 text-base border-b bg-white">
            Logs
          </div>
          <div>
            {loggedEvents.map((log) => {
              const arrowInfo = getDirectionArrow(log.direction);
              const isError =
                log.eventName.toLowerCase().includes("error") ||
                log.eventData?.response?.status_details?.error != null;

              const isFunctionCall = log.eventData.type === "function_call";
              const eventStyles = getEventBadgeStyles(log);

              return (
                <div
                  key={log.id}
                  className={`border-t border-gray-200 py-2 px-6 font-mono ${eventStyles}`}
                >
                  <div
                    onClick={() => toggleExpand(log.id)}
                    className="flex items-center justify-between cursor-pointer"
                  >
                    <div className="flex items-center flex-1">
                      <span
                        style={{ color: arrowInfo.color }}
                        className="ml-1 mr-2"
                      >
                        {arrowInfo.symbol}
                      </span>
                      <span
                        className={
                          "flex-1 text-sm " +
                          (isError
                            ? "text-red-600"
                            : isFunctionCall
                              ? "text-blue-700 font-medium"
                              : "text-gray-800")
                        }
                      >
                        {log.eventName}
                      </span>
                    </div>
                    <div className="text-gray-500 ml-1 text-xs whitespace-nowrap">
                      {log.timestamp}
                    </div>
                  </div>

                  {log.expanded && (
                    <div className="text-gray-800 text-left">
                      {isFunctionCall
                        ? renderFunctionCallDetails(log)
                        : log.eventData && (
                            <pre className="border-l-2 ml-1 border-gray-200 whitespace-pre-wrap break-words font-mono text-xs mb-2 mt-2 pl-2">
                              {JSON.stringify(log.eventData, null, 2)}
                            </pre>
                          )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default Events;
