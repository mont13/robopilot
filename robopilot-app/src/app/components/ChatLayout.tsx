"use client";

import React, { useState, useEffect } from "react";
import { useAppSelector } from "@/app/lib/hooks";
import { selectSettings } from "@/app/lib/features/settings/settingsSlice";

interface ChatLayoutProps {
  sidebar: React.ReactNode;
  children: React.ReactNode;
  onSidebarToggle?: (collapsed: boolean) => void;
}

const ChatLayout: React.FC<ChatLayoutProps> = ({
  sidebar,
  children,
  onSidebarToggle,
}) => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { isMobile } = useAppSelector(selectSettings);

  // Handle sidebar toggle
  const handleToggleSidebar = () => {
    const newCollapsed = !isSidebarCollapsed;
    setIsSidebarCollapsed(newCollapsed);
    onSidebarToggle?.(newCollapsed);
  };

  // Handle mobile menu toggle
  const handleToggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  // Close mobile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isMobileMenuOpen && isMobile) {
        const target = event.target as Element;
        const sidebar = document.getElementById("mobile-sidebar");
        const toggleButton = document.getElementById("mobile-sidebar-toggle");

        if (
          sidebar &&
          !sidebar.contains(target) &&
          toggleButton &&
          !toggleButton.contains(target)
        ) {
          setIsMobileMenuOpen(false);
        }
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isMobileMenuOpen, isMobile]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && isMobileMenuOpen) {
        setIsMobileMenuOpen(false);
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isMobileMenuOpen]);

  if (isMobile) {
    return (
      <div className="flex h-screen bg-gray-50">
        {/* Mobile Overlay */}
        {isMobileMenuOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={() => setIsMobileMenuOpen(false)}
          />
        )}

        {/* Mobile Sidebar */}
        <div
          id="mobile-sidebar"
          className={`fixed left-0 top-0 h-full w-full max-w-sm bg-gray-900 shadow-2xl transform transition-transform duration-300 ease-in-out z-50 ${
            isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          {/* Mobile Sidebar Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-700">
            <h2 className="text-lg font-semibold text-white">Chat History</h2>
            <button
              onClick={() => setIsMobileMenuOpen(false)}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <div className="flex-1 overflow-hidden">{sidebar}</div>
        </div>

        {/* Mobile Main Content */}
        <div className="flex-1 flex flex-col min-w-0 bg-white">
          {/* Mobile Header with Menu Toggle */}
          <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 shadow-sm safe-area-top">
            <button
              id="mobile-sidebar-toggle"
              onClick={handleToggleMobileMenu}
              className="p-3 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors touch-manipulation"
              aria-label="Toggle sidebar"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            <h1 className="text-lg font-semibold text-gray-900 truncate px-4">
              RoboPilot
            </h1>
            <div className="w-12" /> {/* Spacer for centering */}
          </div>

          {/* Mobile Chat Area */}
          <div className="flex-1 overflow-hidden safe-area-bottom">
            {children}
          </div>
        </div>
      </div>
    );
  }

  // Desktop Layout
  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Desktop Sidebar */}
      <div
        className={`bg-gray-900 text-white flex-shrink-0 transition-all duration-300 ease-in-out flex flex-col overflow-hidden ${
          isSidebarCollapsed ? "w-16" : "w-64"
        }`}
      >
        {/* Sidebar Header */}
        <div
          className={`border-b border-gray-700 flex-shrink-0 ${isSidebarCollapsed ? "p-2" : "p-3"}`}
        >
          <div className="flex items-center justify-between">
            {!isSidebarCollapsed && (
              <h1 className="text-lg font-semibold truncate">RoboPilot</h1>
            )}
            <button
              onClick={handleToggleSidebar}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
              aria-label={
                isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"
              }
            >
              <svg
                className={`w-5 h-5 transition-transform duration-300 ${
                  isSidebarCollapsed ? "rotate-180" : ""
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Sidebar Content */}
        <div className="flex-1 overflow-hidden relative">
          {sidebar}

          {/* Fade effect at bottom */}
          <div className="absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-gray-900 to-transparent pointer-events-none" />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Centered Chat Container */}
        <div className="flex-1 flex justify-center py-6 px-4 overflow-hidden">
          <div className="w-full max-w-4xl flex flex-col min-h-0">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatLayout;
