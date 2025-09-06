import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Image,
  Switch,
  TextInput,
  RefreshControl,
  Modal,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import useUserStore from "../stores/useUserStore";
import useAppPersistStore from "../stores/useAppPersistStore";
import * as Haptics from "expo-haptics";

interface UserProfileProps {
  navigation?: any;
  onClose?: () => void;
  isModal?: boolean;
}

const UserProfile: React.FC<UserProfileProps> = ({
  navigation,
  onClose,
  isModal = false,
}) => {
  const {
    user,
    license,
    authProviders,
    isLoading,
    tokenUsage,
    hasActiveAuthProviderConnection,
    showAuthProviderConnectionError,
    updateSettings,
    refreshAuthProviders,
    getUserLicense,
    getUserLicenseStats,
    deleteAccount,
    resetAuthProviderConnectionError,
  } = useUserStore();

  const { theme, setTheme, logout, analyticsEnabled, setAnalyticsEnabled } =
    useAppPersistStore();

  const [editingProfile, setEditingProfile] = useState(false);
  const [firstName, setFirstName] = useState(user?.firstName || "");
  const [lastName, setLastName] = useState(user?.lastName || "");
  const [username, setUsername] = useState(user?.username || "");
  const [refreshing, setRefreshing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (user) {
      setFirstName(user.firstName || "");
      setLastName(user.lastName || "");
      setUsername(user.username || "");
    }
  }, [user]);

  useEffect(() => {
    getUserLicense();
    getUserLicenseStats();
  }, [getUserLicense, getUserLicenseStats]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        refreshAuthProviders(),
        getUserLicense(),
        getUserLicenseStats(),
      ]);
    } finally {
      setRefreshing(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      await updateSettings({
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        username: username.trim(),
      });
      setEditingProfile(false);
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      Alert.alert("Success", "Profile updated successfully");
    } catch (error) {
      Alert.alert("Error", "Failed to update profile");
      console.error("Profile update error:", error);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await deleteAccount();
      Alert.alert("Account Deleted", "Your account has been deleted");
      if (navigation) {
        navigation.replace("Login");
      }
    } catch (error) {
      Alert.alert("Error", "Failed to delete account");
    }
  };

  const handleLogout = async () => {
    Alert.alert("Logout", "Are you sure you want to logout?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Logout",
        style: "destructive",
        onPress: async () => {
          await logout();
          if (navigation) {
            navigation.replace("Login");
          } else if (onClose) {
            onClose();
          }
        },
      },
    ]);
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <View style={styles.avatarContainer}>
        {user?.avatar ? (
          <Image source={{ uri: user.avatar }} style={styles.avatar} />
        ) : (
          <View style={styles.avatarPlaceholder}>
            <Ionicons name="person" size={32} color="white" />
          </View>
        )}

        {/* Online Status Indicator */}
        <View style={styles.statusIndicator}>
          <View
            style={[
              styles.statusDot,
              {
                backgroundColor: hasActiveAuthProviderConnection
                  ? "#10B981"
                  : "#EF4444",
              },
            ]}
          />
        </View>
      </View>

      <Text style={styles.displayName}>
        {user?.displayName || "Unknown User"}
      </Text>
      <Text style={styles.email}>{user?.email || "No email"}</Text>

      {user?.isVerified && (
        <View style={styles.verifiedBadge}>
          <Ionicons name="checkmark-circle" size={16} color="#10B981" />
          <Text style={styles.verifiedText}>Verified</Text>
        </View>
      )}
    </View>
  );

  const renderProfileSection = () => (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Profile Information</Text>
        <TouchableOpacity
          style={styles.editButton}
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            setEditingProfile(!editingProfile);
          }}
        >
          <Ionicons
            name={editingProfile ? "close" : "pencil"}
            size={16}
            color={editingProfile ? "#EF4444" : "#3B82F6"}
          />
          <Text
            style={[styles.editButtonText, editingProfile && styles.cancelText]}
          >
            {editingProfile ? "Cancel" : "Edit"}
          </Text>
        </TouchableOpacity>
      </View>

      {editingProfile ? (
        <View style={styles.editForm}>
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>First Name</Text>
            <TextInput
              style={styles.textInput}
              value={firstName}
              onChangeText={setFirstName}
              placeholder="Enter first name"
              autoCapitalize="words"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Last Name</Text>
            <TextInput
              style={styles.textInput}
              value={lastName}
              onChangeText={setLastName}
              placeholder="Enter last name"
              autoCapitalize="words"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Username</Text>
            <TextInput
              style={styles.textInput}
              value={username}
              onChangeText={setUsername}
              placeholder="Enter username"
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>

          <TouchableOpacity
            style={styles.saveButton}
            onPress={handleSaveProfile}
          >
            <Text style={styles.saveButtonText}>Save Changes</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.profileInfo}>
          <View style={styles.infoRow}>
            <Ionicons name="person-outline" size={16} color="#6B7280" />
            <Text style={styles.infoLabel}>Name:</Text>
            <Text style={styles.infoValue}>
              {user?.firstName || user?.lastName
                ? `${user.firstName || ""} ${user.lastName || ""}`.trim()
                : "Not set"}
            </Text>
          </View>

          <View style={styles.infoRow}>
            <Ionicons name="at-outline" size={16} color="#6B7280" />
            <Text style={styles.infoLabel}>Username:</Text>
            <Text style={styles.infoValue}>{user?.username || "Not set"}</Text>
          </View>

          <View style={styles.infoRow}>
            <Ionicons name="mail-outline" size={16} color="#6B7280" />
            <Text style={styles.infoLabel}>Email:</Text>
            <Text style={styles.infoValue}>{user?.email || "Not set"}</Text>
          </View>
        </View>
      )}
    </View>
  );

  const renderLicenseSection = () => {
    if (!license) {
      return (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>License & Usage</Text>
          <Text style={styles.noDataText}>
            No license information available
          </Text>
        </View>
      );
    }

    const usagePercentage = license.usagePercentage;
    const remaining = license.getRemainingUsage();

    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>License & Usage</Text>

        <View style={styles.licenseHeader}>
          <View style={styles.planBadge}>
            <Text style={styles.planText}>{license.plan.toUpperCase()}</Text>
          </View>
          <View
            style={[
              styles.statusBadge,
              { backgroundColor: license.isActive ? "#DCFCE7" : "#FEE2E2" },
            ]}
          >
            <Text
              style={[
                styles.statusText,
                { color: license.isActive ? "#166534" : "#991B1B" },
              ]}
            >
              {license.status.toUpperCase()}
            </Text>
          </View>
        </View>

        {/* Usage Statistics */}
        {(usagePercentage.messages !== undefined ||
          usagePercentage.tokens !== undefined) && (
          <View style={styles.usageSection}>
            <Text style={styles.subsectionTitle}>Usage</Text>

            {usagePercentage.messages !== undefined && (
              <View style={styles.usageItem}>
                <View style={styles.usageHeader}>
                  <Text style={styles.usageLabel}>Messages</Text>
                  <Text style={styles.usageValue}>
                    {remaining.messages || 0} remaining
                  </Text>
                </View>
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      {
                        width: `${Math.min(usagePercentage.messages, 100)}%`,
                        backgroundColor:
                          usagePercentage.messages > 80 ? "#EF4444" : "#3B82F6",
                      },
                    ]}
                  />
                </View>
                <Text style={styles.percentageText}>
                  {usagePercentage.messages.toFixed(1)}% used
                </Text>
              </View>
            )}

            {usagePercentage.tokens !== undefined && (
              <View style={styles.usageItem}>
                <View style={styles.usageHeader}>
                  <Text style={styles.usageLabel}>Tokens</Text>
                  <Text style={styles.usageValue}>
                    {remaining.tokens || 0} remaining
                  </Text>
                </View>
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      {
                        width: `${Math.min(usagePercentage.tokens, 100)}%`,
                        backgroundColor:
                          usagePercentage.tokens > 80 ? "#EF4444" : "#3B82F6",
                      },
                    ]}
                  />
                </View>
                <Text style={styles.percentageText}>
                  {usagePercentage.tokens.toFixed(1)}% used
                </Text>
              </View>
            )}
          </View>
        )}

        {/* Features */}
        <View style={styles.featuresSection}>
          <Text style={styles.subsectionTitle}>Features</Text>
          <View style={styles.featuresList}>
            <View style={styles.featureItem}>
              <Ionicons
                name={
                  license.canUseFeature("voiceEnabled")
                    ? "checkmark-circle"
                    : "close-circle"
                }
                size={16}
                color={
                  license.canUseFeature("voiceEnabled") ? "#10B981" : "#EF4444"
                }
              />
              <Text style={styles.featureText}>Voice Input & TTS</Text>
            </View>
            <View style={styles.featureItem}>
              <Ionicons
                name={
                  license.canUseFeature("apiAccess")
                    ? "checkmark-circle"
                    : "close-circle"
                }
                size={16}
                color={
                  license.canUseFeature("apiAccess") ? "#10B981" : "#EF4444"
                }
              />
              <Text style={styles.featureText}>API Access</Text>
            </View>
            <View style={styles.featureItem}>
              <Ionicons
                name={
                  license.canUseFeature("prioritySupport")
                    ? "checkmark-circle"
                    : "close-circle"
                }
                size={16}
                color={
                  license.canUseFeature("prioritySupport")
                    ? "#10B981"
                    : "#EF4444"
                }
              />
              <Text style={styles.featureText}>Priority Support</Text>
            </View>
            <View style={styles.featureItem}>
              <Ionicons
                name={
                  license.canUseFeature("customModels")
                    ? "checkmark-circle"
                    : "close-circle"
                }
                size={16}
                color={
                  license.canUseFeature("customModels") ? "#10B981" : "#EF4444"
                }
              />
              <Text style={styles.featureText}>Custom Models</Text>
            </View>
          </View>
        </View>
      </View>
    );
  };

  const renderAuthProvidersSection = () => (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Authentication</Text>
        <TouchableOpacity
          style={styles.refreshButton}
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            refreshAuthProviders();
          }}
        >
          <Ionicons name="refresh" size={14} color="#3B82F6" />
          <Text style={styles.refreshButtonText}>Refresh</Text>
        </TouchableOpacity>
      </View>

      {authProviders.length === 0 ? (
        <Text style={styles.noDataText}>
          No authentication providers configured
        </Text>
      ) : (
        <View style={styles.providersList}>
          {authProviders.map((provider) => (
            <View key={provider.id} style={styles.providerItem}>
              <View style={styles.providerIcon}>
                <Ionicons name="link" size={16} color="#6B7280" />
              </View>
              <View style={styles.providerInfo}>
                <Text style={styles.providerName}>{provider.name}</Text>
                <Text style={styles.providerType}>{provider.provider}</Text>
              </View>
              <View
                style={[
                  styles.connectionStatus,
                  {
                    backgroundColor: provider.userIsLogged
                      ? "#DCFCE7"
                      : "#FEE2E2",
                  },
                ]}
              >
                <Text
                  style={[
                    styles.connectionStatusText,
                    { color: provider.userIsLogged ? "#166534" : "#991B1B" },
                  ]}
                >
                  {provider.userIsLogged ? "Connected" : "Disconnected"}
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}
    </View>
  );

  const renderSettingsSection = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Settings</Text>

      {/* Theme Setting */}
      <View style={styles.settingItem}>
        <View style={styles.settingInfo}>
          <Ionicons name="color-palette-outline" size={20} color="#6B7280" />
          <Text style={styles.settingLabel}>Theme</Text>
        </View>
        <View style={styles.themeSelector}>
          {["light", "dark", "system"].map((themeOption) => (
            <TouchableOpacity
              key={themeOption}
              style={[
                styles.themeButton,
                theme === themeOption && styles.themeButtonActive,
              ]}
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                setTheme(themeOption as any);
              }}
            >
              <Text
                style={[
                  styles.themeButtonText,
                  theme === themeOption && styles.themeButtonTextActive,
                ]}
              >
                {themeOption.charAt(0).toUpperCase() + themeOption.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Analytics Setting */}
      <View style={styles.settingItem}>
        <View style={styles.settingInfo}>
          <Ionicons name="analytics-outline" size={20} color="#6B7280" />
          <View>
            <Text style={styles.settingLabel}>Analytics</Text>
            <Text style={styles.settingDescription}>Help improve the app</Text>
          </View>
        </View>
        <Switch
          value={analyticsEnabled}
          onValueChange={(value) => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            setAnalyticsEnabled(value);
          }}
          trackColor={{ false: "#D1D5DB", true: "#93C5FD" }}
          thumbColor={analyticsEnabled ? "#3B82F6" : "#9CA3AF"}
        />
      </View>
    </View>
  );

  const renderActionsSection = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Actions</Text>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Ionicons name="log-out-outline" size={20} color="#F59E0B" />
        <Text style={styles.logoutButtonText}>Sign Out</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.deleteButton}
        onPress={() => setShowDeleteConfirm(true)}
      >
        <Ionicons name="trash-outline" size={20} color="#EF4444" />
        <Text style={styles.deleteButtonText}>Delete Account</Text>
      </TouchableOpacity>
    </View>
  );

  if (isLoading && !user) {
    return (
      <View style={[styles.container, styles.centered]}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.loadingText}>Loading profile...</Text>
      </View>
    );
  }

  if (!user) {
    return (
      <View style={[styles.container, styles.centered]}>
        <Ionicons name="alert-circle-outline" size={48} color="#EF4444" />
        <Text style={styles.errorText}>User not found</Text>
        <TouchableOpacity style={styles.retryButton} onPress={handleLogout}>
          <Text style={styles.retryButtonText}>Back to Login</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const content = (
    <ScrollView
      style={styles.scrollView}
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={handleRefresh}
          colors={["#3B82F6"]}
          tintColor="#3B82F6"
        />
      }
      showsVerticalScrollIndicator={false}
    >
      {/* Connection Error Banner */}
      {showAuthProviderConnectionError && (
        <View style={styles.errorBanner}>
          <View style={styles.errorBannerContent}>
            <Ionicons name="warning-outline" size={20} color="#D97706" />
            <Text style={styles.errorBannerText}>
              No active authentication provider connection found
            </Text>
          </View>
          <TouchableOpacity
            style={styles.errorBannerButton}
            onPress={resetAuthProviderConnectionError}
          >
            <Text style={styles.errorBannerButtonText}>Dismiss</Text>
          </TouchableOpacity>
        </View>
      )}

      {renderHeader()}
      {renderProfileSection()}
      {renderLicenseSection()}
      {renderAuthProvidersSection()}
      {renderSettingsSection()}
      {renderActionsSection()}
    </ScrollView>
  );

  if (isModal) {
    return (
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Profile</Text>
          {onClose && (
            <TouchableOpacity style={styles.modalCloseButton} onPress={onClose}>
              <Ionicons name="close" size={24} color="#6B7280" />
            </TouchableOpacity>
          )}
        </View>
        {content}
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {content}

      {/* Delete Confirmation Modal */}
      <Modal
        visible={showDeleteConfirm}
        transparent
        animationType="fade"
        onRequestClose={() => setShowDeleteConfirm(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.confirmDialog}>
            <Ionicons name="warning" size={48} color="#EF4444" />
            <Text style={styles.confirmTitle}>Delete Account</Text>
            <Text style={styles.confirmMessage}>
              Are you sure you want to delete your account? This action cannot
              be undone.
            </Text>
            <View style={styles.confirmButtons}>
              <TouchableOpacity
                style={styles.confirmCancelButton}
                onPress={() => setShowDeleteConfirm(false)}
              >
                <Text style={styles.confirmCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.confirmDeleteButton}
                onPress={() => {
                  setShowDeleteConfirm(false);
                  handleDeleteAccount();
                }}
              >
                <Text style={styles.confirmDeleteText}>Delete</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F9FAFB",
  },
  modalContainer: {
    flex: 1,
    backgroundColor: "#F9FAFB",
  },
  modalHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
    backgroundColor: "white",
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: "600",
    color: "#1F2937",
  },
  modalCloseButton: {
    padding: 4,
  },
  centered: {
    justifyContent: "center",
    alignItems: "center",
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: "#6B7280",
  },
  errorText: {
    fontSize: 18,
    color: "#EF4444",
    fontWeight: "500",
    marginTop: 16,
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: "#3B82F6",
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },
  errorBanner: {
    backgroundColor: "#FEF3C7",
    borderColor: "#F59E0B",
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
  },
  errorBannerContent: {
    flexDirection: "row",
    alignItems: "flex-start",
    flex: 1,
    gap: 12,
  },
  errorBannerText: {
    color: "#92400E",
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
  },
  errorBannerButton: {
    backgroundColor: "#F59E0B",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginLeft: 12,
  },
  errorBannerButtonText: {
    color: "white",
    fontSize: 12,
    fontWeight: "600",
  },
  header: {
    alignItems: "center",
    marginBottom: 24,
    backgroundColor: "white",
    padding: 24,
    borderRadius: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  avatarContainer: {
    position: "relative",
    marginBottom: 16,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
  },
  avatarPlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: "#6B7280",
    alignItems: "center",
    justifyContent: "center",
  },
  statusIndicator: {
    position: "absolute",
    bottom: 4,
    right: 4,
    backgroundColor: "white",
    borderRadius: 12,
    padding: 2,
  },
  statusDot: {
    width: 16,
    height: 16,
    borderRadius: 8,
  },
  displayName: {
    fontSize: 24,
    fontWeight: "700",
    color: "#1F2937",
    marginBottom: 4,
  },
  email: {
    fontSize: 16,
    color: "#6B7280",
    marginBottom: 12,
  },
  verifiedBadge: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#DCFCE7",
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  verifiedText: {
    fontSize: 12,
    color: "#166534",
    fontWeight: "600",
  },
  section: {
    backgroundColor: "white",
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1F2937",
  },
  editButton: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#EFF6FF",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    gap: 4,
  },
  editButtonText: {
    color: "#3B82F6",
    fontSize: 14,
    fontWeight: "600",
  },
  cancelText: {
    color: "#EF4444",
  },
  refreshButton: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#EFF6FF",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    gap: 4,
  },
  refreshButtonText: {
    color: "#3B82F6",
    fontSize: 12,
    fontWeight: "600",
  },
  editForm: {
    gap: 16,
  },
  inputGroup: {
    gap: 6,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: "#374151",
  },
  textInput: {
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: "#F9FAFB",
    color: "#1F2937",
  },
  saveButton: {
    backgroundColor: "#10B981",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
    marginTop: 8,
  },
  saveButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "700",
  },
  profileInfo: {
    gap: 16,
  },
  infoRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  infoLabel: {
    fontSize: 14,
    color: "#6B7280",
    width: 80,
  },
  infoValue: {
    fontSize: 16,
    color: "#1F2937",
    flex: 1,
    fontWeight: "500",
  },
  noDataText: {
    fontSize: 14,
    color: "#9CA3AF",
    textAlign: "center",
    fontStyle: "italic",
    paddingVertical: 20,
  },
  licenseHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 20,
  },
  planBadge: {
    backgroundColor: "#EFF6FF",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
  },
  planText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#3B82F6",
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  statusText: {
    fontSize: 12,
    fontWeight: "700",
  },
  usageSection: {
    marginBottom: 20,
  },
  subsectionTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#374151",
    marginBottom: 12,
  },
  usageItem: {
    marginBottom: 16,
  },
  usageHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  usageLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: "#374151",
  },
  usageValue: {
    fontSize: 14,
    color: "#6B7280",
  },
  progressBar: {
    height: 6,
    backgroundColor: "#E5E7EB",
    borderRadius: 3,
    overflow: "hidden",
    marginBottom: 4,
  },
  progressFill: {
    height: "100%",
    borderRadius: 3,
  },
  percentageText: {
    fontSize: 12,
    color: "#6B7280",
  },
  featuresSection: {
    gap: 12,
  },
  featuresList: {
    gap: 12,
  },
  featureItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  featureText: {
    fontSize: 14,
    color: "#374151",
  },
  providersList: {
    gap: 12,
  },
  providerItem: {
    flexDirection: "row",
    alignItems: "center",
    padding: 12,
    backgroundColor: "#F9FAFB",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    gap: 12,
  },
  providerIcon: {
    width: 32,
    height: 32,
    backgroundColor: "#E5E7EB",
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  providerInfo: {
    flex: 1,
  },
  providerName: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1F2937",
  },
  providerType: {
    fontSize: 12,
    color: "#6B7280",
    textTransform: "capitalize",
  },
  connectionStatus: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  connectionStatusText: {
    fontSize: 11,
    fontWeight: "600",
  },
  settingItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
  },
  settingInfo: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    flex: 1,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: "500",
    color: "#1F2937",
  },
  settingDescription: {
    fontSize: 12,
    color: "#6B7280",
    marginTop: 2,
  },
  themeSelector: {
    flexDirection: "row",
    gap: 6,
  },
  themeButton: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: "#F3F4F6",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  themeButtonActive: {
    backgroundColor: "#3B82F6",
    borderColor: "#3B82F6",
  },
  themeButtonText: {
    fontSize: 11,
    color: "#6B7280",
    fontWeight: "500",
  },
  themeButtonTextActive: {
    color: "white",
  },
  logoutButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FEF3C7",
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    gap: 8,
  },
  logoutButtonText: {
    color: "#F59E0B",
    fontSize: 16,
    fontWeight: "600",
  },
  deleteButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FEE2E2",
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  deleteButtonText: {
    color: "#EF4444",
    fontSize: 16,
    fontWeight: "600",
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  confirmDialog: {
    backgroundColor: "white",
    borderRadius: 16,
    padding: 24,
    alignItems: "center",
    width: "100%",
    maxWidth: 320,
  },
  confirmTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: "#1F2937",
    marginTop: 16,
    marginBottom: 8,
  },
  confirmMessage: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
    lineHeight: 20,
    marginBottom: 24,
  },
  confirmButtons: {
    flexDirection: "row",
    gap: 12,
    width: "100%",
  },
  confirmCancelButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    alignItems: "center",
  },
  confirmCancelText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#6B7280",
  },
  confirmDeleteButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: "#EF4444",
    alignItems: "center",
  },
  confirmDeleteText: {
    fontSize: 14,
    fontWeight: "600",
    color: "white",
  },
});

export default UserProfile;
