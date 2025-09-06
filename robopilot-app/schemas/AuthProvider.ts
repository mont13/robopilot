export interface AuthProvider {
  id: string;
  name: string;
  type: 'oauth' | 'social' | 'enterprise';
  provider: 'google' | 'apple' | 'facebook' | 'github' | 'microsoft' | 'custom';
  clientId?: string;
  isEnabled: boolean;
  userIsLogged: boolean;
  config?: {
    scopes?: string[];
    redirectUri?: string;
    additionalParams?: Record<string, any>;
  };
  userInfo?: {
    providerId: string;
    email?: string;
    name?: string;
    avatar?: string;
    accessToken?: string;
    refreshToken?: string;
    expiresAt?: string;
  };
  createdAt?: string;
  updatedAt?: string;
}

export class AuthProviderModel implements AuthProvider {
  id: string;
  name: string;
  type: 'oauth' | 'social' | 'enterprise';
  provider: 'google' | 'apple' | 'facebook' | 'github' | 'microsoft' | 'custom';
  clientId?: string;
  isEnabled: boolean;
  userIsLogged: boolean;
  config?: AuthProvider['config'];
  userInfo?: AuthProvider['userInfo'];
  createdAt?: string;
  updatedAt?: string;

  constructor(data: Partial<AuthProvider>) {
    this.id = data.id || '';
    this.name = data.name || '';
    this.type = data.type || 'oauth';
    this.provider = data.provider || 'custom';
    this.clientId = data.clientId;
    this.isEnabled = data.isEnabled ?? true;
    this.userIsLogged = data.userIsLogged ?? false;
    this.config = data.config;
    this.userInfo = data.userInfo;
    this.createdAt = data.createdAt;
    this.updatedAt = data.updatedAt;
  }

  clone(): AuthProviderModel {
    return new AuthProviderModel({
      id: this.id,
      name: this.name,
      type: this.type,
      provider: this.provider,
      clientId: this.clientId,
      isEnabled: this.isEnabled,
      userIsLogged: this.userIsLogged,
      config: this.config ? { ...this.config } : undefined,
      userInfo: this.userInfo ? { ...this.userInfo } : undefined,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
    });
  }

  get isConnected(): boolean {
    return this.userIsLogged && !!this.userInfo?.accessToken;
  }

  get isExpired(): boolean {
    if (!this.userInfo?.expiresAt) return false;
    return new Date(this.userInfo.expiresAt) < new Date();
  }

  get needsRefresh(): boolean {
    return this.isConnected && this.isExpired && !!this.userInfo?.refreshToken;
  }

  toJSON(): AuthProvider {
    return {
      id: this.id,
      name: this.name,
      type: this.type,
      provider: this.provider,
      clientId: this.clientId,
      isEnabled: this.isEnabled,
      userIsLogged: this.userIsLogged,
      config: this.config,
      userInfo: this.userInfo,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
    };
  }
}
