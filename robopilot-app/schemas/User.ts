export interface User {
  id: string;
  email: string;
  username?: string;
  firstName?: string;
  lastName?: string;
  avatar?: string;
  isActive: boolean;
  isVerified: boolean;
  createdAt?: string;
  updatedAt?: string;
  preferences?: {
    theme?: 'light' | 'dark' | 'system';
    language?: string;
    notifications?: {
      push?: boolean;
      email?: boolean;
      sms?: boolean;
    };
    privacy?: {
      shareData?: boolean;
      publicProfile?: boolean;
    };
  };
  subscription?: {
    plan?: string;
    status?: string;
    expiresAt?: string;
  };
}

export class UserModel implements User {
  id: string;
  email: string;
  username?: string;
  firstName?: string;
  lastName?: string;
  avatar?: string;
  isActive: boolean;
  isVerified: boolean;
  createdAt?: string;
  updatedAt?: string;
  preferences?: User['preferences'];
  subscription?: User['subscription'];

  constructor(data: Partial<User>) {
    this.id = data.id || '';
    this.email = data.email || '';
    this.username = data.username;
    this.firstName = data.firstName;
    this.lastName = data.lastName;
    this.avatar = data.avatar;
    this.isActive = data.isActive ?? true;
    this.isVerified = data.isVerified ?? false;
    this.createdAt = data.createdAt;
    this.updatedAt = data.updatedAt;
    this.preferences = data.preferences || {
      theme: 'system',
      language: 'en',
      notifications: {
        push: true,
        email: true,
        sms: false,
      },
      privacy: {
        shareData: false,
        publicProfile: false,
      },
    };
    this.subscription = data.subscription;
  }

  clone(): UserModel {
    return new UserModel({
      id: this.id,
      email: this.email,
      username: this.username,
      firstName: this.firstName,
      lastName: this.lastName,
      avatar: this.avatar,
      isActive: this.isActive,
      isVerified: this.isVerified,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
      preferences: this.preferences ? { ...this.preferences } : undefined,
      subscription: this.subscription ? { ...this.subscription } : undefined,
    });
  }

  get fullName(): string {
    if (this.firstName && this.lastName) {
      return `${this.firstName} ${this.lastName}`;
    }
    return this.firstName || this.lastName || this.username || this.email;
  }

  get displayName(): string {
    return this.username || this.fullName;
  }

  toJSON(): User {
    return {
      id: this.id,
      email: this.email,
      username: this.username,
      firstName: this.firstName,
      lastName: this.lastName,
      avatar: this.avatar,
      isActive: this.isActive,
      isVerified: this.isVerified,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
      preferences: this.preferences,
      subscription: this.subscription,
    };
  }
}
