import {
  createConnection,
  LLMConnectionCreate,
  ProviderType,
  TestConnectionResponse,
} from "@/app/api/connections";
import React, { FormEvent, useEffect, useState } from "react";

interface ConnectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnectionCreated: () => void;
}

const initialFormState: LLMConnectionCreate = {
  name: "",
  provider: "openai",
  model_name: "",
  api_key: "",
  base_url: "https://api.openai.com/v1",
  api_version: "2020-10-01",
  is_active: true,
};

const providerOptions: { value: ProviderType; label: string }[] = [
  { value: "openai", label: "OpenAI" },
  { value: "gemini", label: "Google Gemini" },
  { value: "lmstudio", label: "LM Studio" },
  { value: "ollama", label: "Ollama" },
];

export const ConnectionModal: React.FC<ConnectionModalProps> = ({
  isOpen,
  onClose,
  onConnectionCreated,
}) => {
  const [formData, setFormData] =
    useState<LLMConnectionCreate>(initialFormState);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [testResult, setTestResult] = useState<TestConnectionResponse | null>(
    null,
  );

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData(initialFormState);
      setErrors({});
      setTestResult(null);
    }
  }, [isOpen]);

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >,
  ) => {
    const { name, value, type } = e.target;

    // Handle checkbox inputs
    if (type === "checkbox") {
      const checkbox = e.target as HTMLInputElement;
      setFormData((prev) => ({ ...prev, [name]: checkbox.checked }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }

    // Clear errors when field is edited
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Connection name is required";
    }

    if (!formData.model_name.trim()) {
      newErrors.model_name = "Model name is required";
    }

    // API key is required for OpenAI and Gemini
    if (
      (formData.provider === "openai" || formData.provider === "gemini") &&
      !formData.api_key?.trim()
    ) {
      newErrors.api_key = "API key is required for this provider";
    }

    // Base URL is required for all providers
    if (!formData.base_url?.trim()) {
      newErrors.base_url = "Base URL is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      // Prepare form data with "NA" for non-required fields
      const submitData = {
        ...formData,
        api_key:
          (formData.provider === "lmstudio" ||
            formData.provider === "ollama") &&
          !formData.api_key?.trim()
            ? "NA"
            : formData.api_key,
        api_version:
          formData.provider !== "openai" && !formData.api_version?.trim()
            ? "NA"
            : formData.api_version,
      };

      await createConnection(submitData);
      onConnectionCreated();
      onClose();
    } catch (error) {
      console.error("Failed to create connection:", error);
      setErrors({
        form:
          error instanceof Error
            ? error.message
            : "Failed to create connection",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white">
            Create New Connection
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
            aria-label="Close"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4">
          {errors.form && (
            <div className="mb-4 p-2 bg-red-100 border border-red-400 text-red-700 rounded">
              {errors.form}
            </div>
          )}

          {/* Connection Name */}
          <div className="mb-4">
            <label
              htmlFor="name"
              className="block mb-1 font-medium text-gray-700 dark:text-gray-300"
            >
              Connection Name*
            </label>
            <input
              id="name"
              name="name"
              type="text"
              value={formData.name}
              onChange={handleInputChange}
              className={`w-full p-2 border rounded ${
                errors.name
                  ? "border-red-500"
                  : "border-gray-300 dark:border-gray-600"
              } bg-white dark:bg-gray-700 text-gray-900 dark:text-white`}
              placeholder="My OpenAI Connection"
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-500">{errors.name}</p>
            )}
          </div>

          {/* Provider */}
          <div className="mb-4">
            <label
              htmlFor="provider"
              className="block mb-1 font-medium text-gray-700 dark:text-gray-300"
            >
              Provider*
            </label>
            <select
              id="provider"
              name="provider"
              value={formData.provider}
              onChange={(e) => {
                const newProvider = e.target.value as ProviderType;

                setFormData((prev) => ({
                  ...prev,
                  provider: newProvider,
                  model_name: "",
                  // Reset provider-specific fields
                  api_key: "",
                  base_url:
                    newProvider === "ollama"
                      ? "http://host.docker.internal:11434/v1"
                      : newProvider === "lmstudio"
                        ? "http://host.docker.internal:1234/v1"
                        : newProvider === "openai"
                          ? "https://api.openai.com/v1"
                          : newProvider === "gemini"
                            ? "https://generativelanguage.googleapis.com/v1beta/openai"
                            : "",
                  api_version: newProvider === "openai" ? "2020-10-01" : "",
                }));
              }}
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {providerOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Model Name */}
          <div className="mb-4">
            <label
              htmlFor="model_name"
              className="block mb-1 font-medium text-gray-700 dark:text-gray-300"
            >
              Model Name*
            </label>
            <input
              id="model_name"
              name="model_name"
              type="text"
              value={formData.model_name}
              onChange={handleInputChange}
              className={`w-full p-2 border rounded ${
                errors.model_name
                  ? "border-red-500"
                  : "border-gray-300 dark:border-gray-600"
              } bg-white dark:bg-gray-700 text-gray-900 dark:text-white`}
              placeholder={
                formData.provider === "openai"
                  ? "gpt-4o, gpt-4o-mini, gpt-3.5-turbo"
                  : formData.provider === "gemini"
                    ? "gemini-2.0-flash, gemini-1.5-pro"
                    : formData.provider === "ollama"
                      ? "llama3, mistral, codellama"
                      : formData.provider === "lmstudio"
                        ? "model name from LM Studio"
                        : "Enter model name"
              }
            />
            {errors.model_name && (
              <p className="mt-1 text-sm text-red-500">{errors.model_name}</p>
            )}
          </div>

          {/* API Key */}
          <div className="mb-4">
            <label
              htmlFor="api_key"
              className="block mb-1 font-medium text-gray-700 dark:text-gray-300"
            >
              API Key
              {(formData.provider === "openai" ||
                formData.provider === "gemini") &&
                "*"}
            </label>
            <input
              id="api_key"
              name="api_key"
              type="password"
              value={formData.api_key || ""}
              onChange={handleInputChange}
              className={`w-full p-2 border rounded ${
                errors.api_key
                  ? "border-red-500"
                  : "border-gray-300 dark:border-gray-600"
              } bg-white dark:bg-gray-700 text-gray-900 dark:text-white`}
              placeholder={
                formData.provider === "openai"
                  ? "Enter your OpenAI API key"
                  : formData.provider === "gemini"
                    ? "Enter your Google AI API key"
                    : "API key (if required)"
              }
            />
            {errors.api_key && (
              <p className="mt-1 text-sm text-red-500">{errors.api_key}</p>
            )}
          </div>

          {/* Base URL */}
          <div className="mb-4">
            <label
              htmlFor="base_url"
              className="block mb-1 font-medium text-gray-700 dark:text-gray-300"
            >
              Base URL*
            </label>
            <input
              id="base_url"
              name="base_url"
              type="text"
              value={formData.base_url || ""}
              onChange={handleInputChange}
              className={`w-full p-2 border rounded ${
                errors.base_url
                  ? "border-red-500"
                  : "border-gray-300 dark:border-gray-600"
              } bg-white dark:bg-gray-700 text-gray-900 dark:text-white`}
              placeholder={
                formData.provider === "openai"
                  ? "https://api.openai.com/v1"
                  : formData.provider === "gemini"
                    ? "https://generativelanguage.googleapis.com/v1beta/openai"
                    : formData.provider === "lmstudio"
                      ? "http://host.docker.internal:1234/v1"
                      : formData.provider === "ollama"
                        ? "http://host.docker.internal:11434/v1"
                        : "Enter base URL"
              }
            />
            {errors.base_url && (
              <p className="mt-1 text-sm text-red-500">{errors.base_url}</p>
            )}
            {(formData.provider === "ollama" ||
              formData.provider === "lmstudio") && (
              <p className="mt-1 text-xs text-blue-600 dark:text-blue-400">
                💡 Docker users: Use{" "}
                <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">
                  host.docker.internal
                </code>{" "}
                instead of{" "}
                <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">
                  localhost
                </code>
              </p>
            )}
          </div>

          {/* API Version */}
          <div className="mb-4">
            <label
              htmlFor="api_version"
              className="block mb-1 font-medium text-gray-700 dark:text-gray-300"
            >
              API Version{formData.provider === "openai" && "*"}
            </label>
            <input
              id="api_version"
              name="api_version"
              type="text"
              value={formData.api_version || ""}
              onChange={handleInputChange}
              className={`w-full p-2 border rounded ${
                errors.api_version
                  ? "border-red-500"
                  : "border-gray-300 dark:border-gray-600"
              } bg-white dark:bg-gray-700 text-gray-900 dark:text-white`}
              placeholder={
                formData.provider === "openai"
                  ? "2020-10-01"
                  : "API version (if required)"
              }
            />
            {errors.api_version && (
              <p className="mt-1 text-sm text-red-500">{errors.api_version}</p>
            )}
          </div>

          {/* Active Connection */}
          <div className="mb-6">
            <label className="flex items-center">
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    is_active: e.target.checked,
                  }))
                }
                className="h-4 w-4 text-blue-500 focus:ring-blue-400 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Set as active connection
              </span>
            </label>
          </div>

          {/* Test Result Banner */}
          {testResult && (
            <div
              className={`mb-4 p-3 rounded border ${
                testResult.success
                  ? "bg-green-50 border-green-300 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-400"
                  : "bg-red-50 border-red-300 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-400"
              }`}
            >
              <div className="font-medium mb-1">
                {testResult.success
                  ? "Connection successful!"
                  : "Connection failed"}
              </div>
              <div className="text-sm">
                {testResult.success
                  ? testResult.response || "Test message sent successfully."
                  : testResult.error || "Unknown error occurred."}
              </div>
            </div>
          )}

          <div className="flex justify-between mt-6">
            <div className="space-x-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-600 bg-white hover:bg-gray-100 border border-gray-300 rounded"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 text-white bg-blue-500 hover:bg-blue-600 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? "Creating..." : "Create Connection"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ConnectionModal;
