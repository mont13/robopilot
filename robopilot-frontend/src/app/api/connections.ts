import { API_BASE_URL } from "@/app/config/api";

// Types
export interface LLMConnectionBase {
  name: string;
  provider: ProviderType;
  model_name: string;
  base_url?: string | null;
  api_version?: string | null;
  is_active: boolean;
}

export interface LLMConnectionCreate extends LLMConnectionBase {
  api_key?: string | null;
}

export interface LLMConnectionUpdate {
  name?: string | null;
  provider?: ProviderType | null;
  model_name?: string | null;
  base_url?: string | null;
  api_key?: string | null;
  api_version?: string | null;
  is_active?: boolean | null;
  config?: Record<string, any> | null;
}

export interface LLMConnectionResponse extends LLMConnectionBase {
  id: string;
  created_at?: string | null;
  updated_at?: string | null;
  config?: string | null;
}

export interface DefaultConnectionResponse {
  connection_id: string;
  name: string;
  provider: ProviderType;
}

export interface TestConnectionResponse {
  success: boolean;
  response?: string | null;
  error?: string | null;
}

export type ProviderType = "openai" | "ollama";

// List all connections
export async function listConnections(): Promise<LLMConnectionResponse[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/connections/`);
    if (!response.ok) {
      throw new Error(`Failed to list connections: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error listing connections:", error);
    throw error;
  }
}

// Create a new connection
export async function createConnection(
  connection: LLMConnectionCreate,
): Promise<LLMConnectionResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/connections/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(connection),
    });

    if (!response.ok) {
      throw new Error(`Failed to create connection: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error creating connection:", error);
    throw error;
  }
}

// Get a specific connection
export async function getConnection(
  connectionId: string,
): Promise<LLMConnectionResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/connections/${connectionId}`,
    );
    if (!response.ok) {
      throw new Error(`Failed to get connection: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error getting connection ${connectionId}:`, error);
    throw error;
  }
}

// Update a connection
export async function updateConnection(
  connectionId: string,
  updates: LLMConnectionUpdate,
): Promise<LLMConnectionResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/connections/${connectionId}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updates),
      },
    );

    if (!response.ok) {
      throw new Error(`Failed to update connection: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error updating connection ${connectionId}:`, error);
    throw error;
  }
}

// Delete a connection
export async function deleteConnection(connectionId: string): Promise<boolean> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/connections/${connectionId}`,
      {
        method: "DELETE",
      },
    );
    return response.ok;
  } catch (error) {
    console.error(`Error deleting connection ${connectionId}:`, error);
    throw error;
  }
}

// Activate a specific connection
export async function activateConnection(
  connectionId: string,
): Promise<DefaultConnectionResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/connections/${connectionId}/activate`,
      {
        method: "POST",
      },
    );

    if (!response.ok) {
      throw new Error(`Failed to activate connection: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error activating connection ${connectionId}:`, error);
    throw error;
  }
}

// Get the currently active connection
export async function getActiveConnection(): Promise<LLMConnectionResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/connections/active/`);
    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`Failed to get active connection: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error getting active connection:", error);
    throw error;
  }
}

// Check if the server is up and running
export async function checkServerHealth(): Promise<boolean> {
  try {
    // Simply check if the server responds to the connections endpoint
    const response = await fetch(`${API_BASE_URL}/api/connections/`);
    return response.ok;
  } catch (error) {
    console.error("Server health check failed:", error);
    return false;
  }
}
