"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface LLMProvider {
  id: string;
  name: string;
  type: "openai" | "anthropic" | "lmstudio" | "ollama" | "custom";
  enabled: boolean;
  apiKey?: string;
  endpoint?: string;
  model?: string;
  maxTokens?: number;
  temperature?: number;
}

const defaultProviders: LLMProvider[] = [
  {
    id: "openai",
    name: "OpenAI",
    type: "openai",
    enabled: true,
    model: "gpt-4",
    maxTokens: 4096,
    temperature: 0.7,
  },
  {
    id: "anthropic",
    name: "Anthropic Claude",
    type: "anthropic",
    enabled: false,
    model: "claude-3-sonnet",
    maxTokens: 4096,
    temperature: 0.7,
  },
  {
    id: "lmstudio",
    name: "LM Studio",
    type: "lmstudio",
    enabled: false,
    endpoint: "http://localhost:1234/v1",
    model: "local-model",
    maxTokens: 2048,
    temperature: 0.7,
  },
  {
    id: "ollama",
    name: "Ollama",
    type: "ollama",
    enabled: false,
    endpoint: "http://localhost:11434",
    model: "llama2",
    maxTokens: 2048,
    temperature: 0.7,
  },
];

export default function SettingsPage() {
  const router = useRouter();
  const [providers, setProviders] = useState<LLMProvider[]>(defaultProviders);
  const [selectedProvider, setSelectedProvider] = useState<string>("openai");
  const [isTestingConnection, setIsTestingConnection] = useState<string | null>(
    null,
  );

  const handleProviderToggle = (id: string) => {
    setProviders((prev) =>
      prev.map((p) => (p.id === id ? { ...p, enabled: !p.enabled } : p)),
    );
  };

  const handleProviderUpdate = (
    id: string,
    field: keyof LLMProvider,
    value: string | number,
  ) => {
    setProviders((prev) =>
      prev.map((p) => (p.id === id ? { ...p, [field]: value } : p)),
    );
  };

  const handleTestConnection = async (id: string) => {
    setIsTestingConnection(id);
    // Simulate API test
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsTestingConnection(null);
  };

  const handleAddProvider = () => {
    const newProvider: LLMProvider = {
      id: `custom-${Date.now()}`,
      name: "Custom Provider",
      type: "custom",
      enabled: false,
      endpoint: "",
      apiKey: "",
      model: "",
      maxTokens: 2048,
      temperature: 0.7,
    };
    setProviders((prev) => [...prev, newProvider]);
    setSelectedProvider(newProvider.id);
  };

  const handleDeleteProvider = (id: string) => {
    setProviders((prev) => prev.filter((p) => p.id !== id));
    if (selectedProvider === id) {
      setSelectedProvider(providers[0]?.id || "");
    }
  };

  const selectedProviderData = providers.find((p) => p.id === selectedProvider);

  const getProviderIcon = (type: string) => {
    switch (type) {
      case "openai":
        return "🤖";
      case "anthropic":
        return "🧠";
      case "lmstudio":
        return "💻";
      case "ollama":
        return "🦙";
      default:
        return "⚙️";
    }
  };

  const getConnectionStatus = (provider: LLMProvider) => {
    if (!provider.enabled) return "disabled";
    if (isTestingConnection === provider.id) return "testing";
    // Simulate connection status
    return Math.random() > 0.3 ? "connected" : "error";
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => router.back()}
                className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <span>←</span>
                Back
              </button>
              <div className="flex items-center gap-2">
                <svg
                  className="w-6 h-6 text-blue-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
                    clipRule="evenodd"
                  />
                </svg>
                <h1 className="text-2xl font-bold">Settings</h1>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {/* Providers List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold">LLM Providers</h2>
                  <button
                    onClick={handleAddProvider}
                    className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Add
                  </button>
                </div>
              </div>
              <div className="p-6">
                <div className="space-y-2">
                  {providers.map((provider) => {
                    const status = getConnectionStatus(provider);
                    return (
                      <div
                        key={provider.id}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${
                          selectedProvider === provider.id
                            ? "border-blue-500 bg-blue-50"
                            : "border-gray-200 hover:border-blue-300"
                        }`}
                        onClick={() => setSelectedProvider(provider.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="text-xl">
                              {getProviderIcon(provider.type)}
                            </span>
                            <div>
                              <p className="font-medium">{provider.name}</p>
                              <p className="text-sm text-gray-500 capitalize">
                                {provider.type}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <div
                              className={`w-2 h-2 rounded-full ${
                                status === "connected"
                                  ? "bg-green-500"
                                  : status === "testing"
                                    ? "bg-yellow-500 animate-pulse"
                                    : status === "error"
                                      ? "bg-red-500"
                                      : "bg-gray-300"
                              }`}
                            />
                            <label className="flex items-center">
                              <input
                                type="checkbox"
                                checked={provider.enabled}
                                onChange={() =>
                                  handleProviderToggle(provider.id)
                                }
                                className="sr-only"
                              />
                              <div
                                className={`w-10 h-6 rounded-full transition-colors ${provider.enabled ? "bg-blue-600" : "bg-gray-300"}`}
                              >
                                <div
                                  className={`w-4 h-4 bg-white rounded-full transition-transform mt-1 ${provider.enabled ? "translate-x-5" : "translate-x-1"}`}
                                />
                              </div>
                            </label>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Provider Configuration */}
          <div className="lg:col-span-2">
            {selectedProviderData ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">
                        {getProviderIcon(selectedProviderData.type)}
                      </span>
                      <div>
                        <h2 className="text-xl font-semibold">
                          {selectedProviderData.name}
                        </h2>
                        <p className="text-gray-500 capitalize">
                          {selectedProviderData.type} Provider
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {selectedProviderData.type === "custom" && (
                        <button
                          onClick={() =>
                            handleDeleteProvider(selectedProviderData.id)
                          }
                          className="flex items-center gap-2 px-3 py-2 text-red-600 hover:text-red-800 transition-colors"
                        >
                          <svg
                            className="w-4 h-4"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                              clipRule="evenodd"
                            />
                          </svg>
                          Delete
                        </button>
                      )}
                      <button
                        onClick={() =>
                          handleTestConnection(selectedProviderData.id)
                        }
                        disabled={
                          isTestingConnection === selectedProviderData.id
                        }
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                      >
                        {isTestingConnection === selectedProviderData.id ? (
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : null}
                        Test Connection
                      </button>
                    </div>
                  </div>
                </div>
                <div className="p-6">
                  <div className="space-y-6">
                    {/* Basic Settings */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-medium">
                        Basic Configuration
                      </h3>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Provider Name
                        </label>
                        <input
                          type="text"
                          value={selectedProviderData.name}
                          onChange={(e) =>
                            handleProviderUpdate(
                              selectedProviderData.id,
                              "name",
                              e.target.value,
                            )
                          }
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>

                      {(selectedProviderData.type === "lmstudio" ||
                        selectedProviderData.type === "ollama" ||
                        selectedProviderData.type === "custom") && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            API Endpoint
                          </label>
                          <input
                            type="text"
                            value={selectedProviderData.endpoint || ""}
                            onChange={(e) =>
                              handleProviderUpdate(
                                selectedProviderData.id,
                                "endpoint",
                                e.target.value,
                              )
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="http://localhost:1234/v1"
                          />
                        </div>
                      )}

                      {(selectedProviderData.type === "openai" ||
                        selectedProviderData.type === "anthropic" ||
                        selectedProviderData.type === "custom") && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            API Key
                          </label>
                          <input
                            type="password"
                            value={selectedProviderData.apiKey || ""}
                            onChange={(e) =>
                              handleProviderUpdate(
                                selectedProviderData.id,
                                "apiKey",
                                e.target.value,
                              )
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Enter your API key"
                          />
                        </div>
                      )}

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Model
                        </label>
                        <input
                          type="text"
                          value={selectedProviderData.model || ""}
                          onChange={(e) =>
                            handleProviderUpdate(
                              selectedProviderData.id,
                              "model",
                              e.target.value,
                            )
                          }
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          placeholder="Model name"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Max Tokens
                          </label>
                          <input
                            type="number"
                            value={selectedProviderData.maxTokens || 2048}
                            onChange={(e) =>
                              handleProviderUpdate(
                                selectedProviderData.id,
                                "maxTokens",
                                parseInt(e.target.value),
                              )
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            min="1"
                            max="32768"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Temperature
                          </label>
                          <input
                            type="number"
                            value={selectedProviderData.temperature || 0.7}
                            onChange={(e) =>
                              handleProviderUpdate(
                                selectedProviderData.id,
                                "temperature",
                                parseFloat(e.target.value),
                              )
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            min="0"
                            max="2"
                            step="0.1"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Save Button */}
                    <div className="flex justify-end pt-4 border-t border-gray-200">
                      <button
                        onClick={() => {
                          // Save configuration logic here
                          alert("Settings saved!");
                        }}
                        className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        Save Configuration
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                <p className="text-gray-500">Select a provider to configure</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
