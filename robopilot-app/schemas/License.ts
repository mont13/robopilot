export interface License {
  id: string;
  userId: string;
  plan: 'free' | 'basic' | 'premium' | 'enterprise';
  status: 'active' | 'expired' | 'suspended' | 'cancelled';
  features: {
    maxSessions?: number;
    maxMessages?: number;
    maxTokens?: number;
    voiceEnabled?: boolean;
    prioritySupport?: boolean;
    customModels?: boolean;
    apiAccess?: boolean;
    exportData?: boolean;
  };
  usage?: {
    sessionsUsed: number;
    messagesUsed: number;
    tokensUsed: number;
    lastResetAt?: string;
  };
  limits?: {
    dailyMessages?: number;
    monthlyTokens?: number;
    concurrentSessions?: number;
  };
  billing?: {
    amount: number;
    currency: string;
    interval: 'monthly' | 'yearly' | 'lifetime';
    nextBillingDate?: string;
    paymentMethod?: string;
  };
  createdAt?: string;
  updatedAt?: string;
  activatedAt?: string;
  expiresAt?: string;
}

export class LicenseModel implements License {
  id: string;
  userId: string;
  plan: 'free' | 'basic' | 'premium' | 'enterprise';
  status: 'active' | 'expired' | 'suspended' | 'cancelled';
  features: License['features'];
  usage?: License['usage'];
  limits?: License['limits'];
  billing?: License['billing'];
  createdAt?: string;
  updatedAt?: string;
  activatedAt?: string;
  expiresAt?: string;

  constructor(data: Partial<License>) {
    this.id = data.id || '';
    this.userId = data.userId || '';
    this.plan = data.plan || 'free';
    this.status = data.status || 'active';
    this.features = data.features || this.getDefaultFeatures();
    this.usage = data.usage || {
      sessionsUsed: 0,
      messagesUsed: 0,
      tokensUsed: 0,
    };
    this.limits = data.limits || this.getDefaultLimits();
    this.billing = data.billing;
    this.createdAt = data.createdAt;
    this.updatedAt = data.updatedAt;
    this.activatedAt = data.activatedAt;
    this.expiresAt = data.expiresAt;
  }

  private getDefaultFeatures(): License['features'] {
    switch (this.plan) {
      case 'free':
        return {
          maxSessions: 10,
          maxMessages: 100,
          maxTokens: 10000,
          voiceEnabled: false,
          prioritySupport: false,
          customModels: false,
          apiAccess: false,
          exportData: false,
        };
      case 'basic':
        return {
          maxSessions: 50,
          maxMessages: 1000,
          maxTokens: 100000,
          voiceEnabled: true,
          prioritySupport: false,
          customModels: false,
          apiAccess: false,
          exportData: true,
        };
      case 'premium':
        return {
          maxSessions: 200,
          maxMessages: 5000,
          maxTokens: 500000,
          voiceEnabled: true,
          prioritySupport: true,
          customModels: true,
          apiAccess: true,
          exportData: true,
        };
      case 'enterprise':
        return {
          maxSessions: -1, // unlimited
          maxMessages: -1, // unlimited
          maxTokens: -1, // unlimited
          voiceEnabled: true,
          prioritySupport: true,
          customModels: true,
          apiAccess: true,
          exportData: true,
        };
      default:
        return {};
    }
  }

  private getDefaultLimits(): License['limits'] {
    switch (this.plan) {
      case 'free':
        return {
          dailyMessages: 10,
          monthlyTokens: 10000,
          concurrentSessions: 1,
        };
      case 'basic':
        return {
          dailyMessages: 100,
          monthlyTokens: 100000,
          concurrentSessions: 3,
        };
      case 'premium':
        return {
          dailyMessages: 500,
          monthlyTokens: 500000,
          concurrentSessions: 10,
        };
      case 'enterprise':
        return {
          dailyMessages: -1, // unlimited
          monthlyTokens: -1, // unlimited
          concurrentSessions: -1, // unlimited
        };
      default:
        return {};
    }
  }

  clone(): LicenseModel {
    return new LicenseModel({
      id: this.id,
      userId: this.userId,
      plan: this.plan,
      status: this.status,
      features: this.features ? { ...this.features } : undefined,
      usage: this.usage ? { ...this.usage } : undefined,
      limits: this.limits ? { ...this.limits } : undefined,
      billing: this.billing ? { ...this.billing } : undefined,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
      activatedAt: this.activatedAt,
      expiresAt: this.expiresAt,
    });
  }

  get isActive(): boolean {
    return this.status === 'active';
  }

  get isExpired(): boolean {
    if (!this.expiresAt) return false;
    return new Date(this.expiresAt) < new Date();
  }

  get daysUntilExpiration(): number | null {
    if (!this.expiresAt) return null;
    const expiryDate = new Date(this.expiresAt);
    const now = new Date();
    const diffTime = expiryDate.getTime() - now.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }

  get usagePercentage(): {
    sessions?: number;
    messages?: number;
    tokens?: number;
  } {
    const result: { sessions?: number; messages?: number; tokens?: number } = {};

    if (this.features.maxSessions && this.features.maxSessions > 0 && this.usage) {
      result.sessions = (this.usage.sessionsUsed / this.features.maxSessions) * 100;
    }

    if (this.features.maxMessages && this.features.maxMessages > 0 && this.usage) {
      result.messages = (this.usage.messagesUsed / this.features.maxMessages) * 100;
    }

    if (this.features.maxTokens && this.features.maxTokens > 0 && this.usage) {
      result.tokens = (this.usage.tokensUsed / this.features.maxTokens) * 100;
    }

    return result;
  }

  get isNearLimit(): boolean {
    const percentages = this.usagePercentage;
    return Object.values(percentages).some(percentage =>
      percentage !== undefined && percentage >= 80
    );
  }

  get isAtLimit(): boolean {
    const percentages = this.usagePercentage;
    return Object.values(percentages).some(percentage =>
      percentage !== undefined && percentage >= 100
    );
  }

  canUseFeature(feature: keyof License['features']): boolean {
    if (!this.isActive || this.isExpired) return false;
    return this.features[feature] === true;
  }

  getRemainingUsage(): {
    sessions?: number;
    messages?: number;
    tokens?: number;
  } {
    const result: { sessions?: number; messages?: number; tokens?: number } = {};

    if (this.features.maxSessions && this.features.maxSessions > 0 && this.usage) {
      result.sessions = Math.max(0, this.features.maxSessions - this.usage.sessionsUsed);
    }

    if (this.features.maxMessages && this.features.maxMessages > 0 && this.usage) {
      result.messages = Math.max(0, this.features.maxMessages - this.usage.messagesUsed);
    }

    if (this.features.maxTokens && this.features.maxTokens > 0 && this.usage) {
      result.tokens = Math.max(0, this.features.maxTokens - this.usage.tokensUsed);
    }

    return result;
  }

  toJSON(): License {
    return {
      id: this.id,
      userId: this.userId,
      plan: this.plan,
      status: this.status,
      features: this.features,
      usage: this.usage,
      limits: this.limits,
      billing: this.billing,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
      activatedAt: this.activatedAt,
      expiresAt: this.expiresAt,
    };
  }
}
