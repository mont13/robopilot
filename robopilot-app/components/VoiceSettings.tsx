import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Switch,
  ScrollView,
  ActivityIndicator,
  Alert,
  Platform,
  Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Picker } from '@react-native-picker/picker';
import Slider from '@react-native-community/slider';
import * as Haptics from 'expo-haptics';
import { VoiceSettings } from '../types/voice';

interface VoiceSettingsProps {
  isVisible: boolean;
  onClose: () => void;
  currentSettings: VoiceSettings;
  onSettingsChange: (settings: VoiceSettings) => void;
  voices?: any[];
  connections?: any[];
  activeConnection?: any;
  onConnectionSelect?: (connectionId: string) => void;
}

export default function VoiceSettings({
  isVisible,
  onClose,
  currentSettings,
  onSettingsChange,
  voices = [],
  connections = [],
  activeConnection,
  onConnectionSelect,
}: VoiceSettingsProps) {
  const [settings, setSettings] = useState<VoiceSettings>(currentSettings);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    model: true,
    voice: true,
    tts: true,
    advanced: false,
  });

  useEffect(() => {
    setSettings(currentSettings);
  }, [currentSettings]);

  const handleSave = async () => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onSettingsChange(settings);
    onClose();
  };

  const handleCancel = async () => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setSettings(currentSettings);
    onClose();
  };

  const updateSetting = <K extends keyof VoiceSettings>(
    key: K,
    value: VoiceSettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const toggleSection = async (section: keyof typeof expandedSections) => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const getProviderIcon = (provider: string) => {
    switch (provider?.toLowerCase()) {
      case 'openai':
        return 'logo-apple';
      case 'gemini':
        return 'diamond';
      case 'lmstudio':
        return 'desktop';
      case 'ollama':
        return 'server';
      default:
        return 'cloud';
    }
  };

  const getConnectionStatusColor = (connection: any) => {
    if (!connection) return '#EF4444';
    return connection.is_active ? '#10B981' : '#F59E0B';
  };

  const renderSectionHeader = (
    title: string,
    icon: string,
    sectionKey: keyof typeof expandedSections,
    subtitle?: string
  ) => (
    <TouchableOpacity
      style={styles.sectionHeader}
      onPress={() => toggleSection(sectionKey)}
    >
      <View style={styles.sectionHeaderLeft}>
        <Ionicons name={icon as any} size={20} color="#3B82F6" />
        <View style={styles.sectionHeaderText}>
          <Text style={styles.sectionTitle}>{title}</Text>
          {subtitle && (
            <Text style={styles.sectionSubtitle}>{subtitle}</Text>
          )}
        </View>
      </View>
      <Ionicons
        name={expandedSections[sectionKey] ? 'chevron-down' : 'chevron-forward'}
        size={20}
        color="#6B7280"
      />
    </TouchableOpacity>
  );

  const renderModelSection = () => (
    <View style={styles.section}>
      {renderSectionHeader(
        'Model Configuration',
        'settings',
        'model',
        'LLM and voice model settings'
      )}

      {expandedSections.model && (
        <View style={styles.sectionContent}>
          {/* LLM Connection */}
          <View style={styles.settingItem}>
            <View style={styles.settingHeader}>
              <Text style={styles.settingLabel}>LLM Connection</Text>
              {activeConnection && (
                <View style={styles.connectionBadge}>
                  <View
                    style={[
                      styles.connectionStatus,
                      { backgroundColor: getConnectionStatusColor(activeConnection) }
                    ]}
                  />
                  <Text style={styles.connectionBadgeText}>Active</Text>
                </View>
              )}
            </View>

            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={activeConnection?.id || ''}
                onValueChange={(connectionId) => {
                  if (onConnectionSelect && connectionId) {
                    onConnectionSelect(connectionId);
                  }
                }}
                style={styles.picker}
                itemStyle={styles.pickerItem}
              >
                <Picker.Item label="Select connection..." value="" />
                {connections.map((conn) => (
                  <Picker.Item
                    key={conn.id}
                    label={`${conn.name} (${conn.provider})`}
                    value={conn.id}
                  />
                ))}
              </Picker>
            </View>

            {activeConnection && (
              <View style={styles.connectionDetails}>
                <View style={styles.connectionDetailRow}>
                  <Ionicons
                    name={getProviderIcon(activeConnection.provider)}
                    size={16}
                    color="#6B7280"
                  />
                  <Text style={styles.connectionDetailText}>
                    {activeConnection.provider} • {activeConnection.model_name}
                  </Text>
                </View>
              </View>
            )}
          </View>

          {/* Voice Model */}
          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Voice Model</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={settings.selectedVoice || ''}
                onValueChange={(voice) => updateSetting('selectedVoice', voice)}
                style={styles.picker}
                itemStyle={styles.pickerItem}
              >
                <Picker.Item label="Select voice..." value="" />
                {voices.map((voice) => (
                  <Picker.Item
                    key={voice.id}
                    label={voice.name || voice.id}
                    value={voice.id}
                  />
                ))}
              </Picker>
            </View>
          </View>

          {/* Language */}
          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Transcription Language</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={settings.language || 'en'}
                onValueChange={(lang) => updateSetting('language', lang)}
                style={styles.picker}
                itemStyle={styles.pickerItem}
              >
                <Picker.Item label="English" value="en" />
                <Picker.Item label="Spanish" value="es" />
                <Picker.Item label="French" value="fr" />
                <Picker.Item label="German" value="de" />
                <Picker.Item label="Italian" value="it" />
                <Picker.Item label="Portuguese" value="pt" />
                <Picker.Item label="Russian" value="ru" />
                <Picker.Item label="Japanese" value="ja" />
                <Picker.Item label="Korean" value="ko" />
                <Picker.Item label="Chinese" value="zh" />
              </Picker>
            </View>
          </View>
        </View>
      )}
    </View>
  );

  const renderVoiceSection = () => (
    <View style={styles.section}>
      {renderSectionHeader(
        'Voice Settings',
        'mic',
        'voice',
        'Audio input and processing'
      )}

      {expandedSections.voice && (
        <View style={styles.sectionContent}>
          {/* Speaker ID */}
          <View style={styles.settingItem}>
            <View style={styles.sliderHeader}>
              <Text style={styles.settingLabel}>Speaker ID</Text>
              <View style={styles.sliderValue}>
                <Text style={styles.sliderValueText}>{settings.speakerId || 0}</Text>
              </View>
            </View>
            <Slider
              style={styles.slider}
              value={settings.speakerId || 0}
              onValueChange={(value) => updateSetting('speakerId', Math.round(value))}
              minimumValue={0}
              maximumValue={9}
              step={1}
              minimumTrackTintColor="#3B82F6"
              maximumTrackTintColor="#E5E7EB"
              thumbStyle={styles.sliderThumb}
            />
            <Text style={styles.settingDescription}>
              Different speaker IDs can change the character of the voice
            </Text>
          </View>

          {/* Voice Activity Detection */}
          <View style={styles.settingItem}>
            <View style={styles.switchRow}>
              <View style={styles.switchInfo}>
                <Text style={styles.settingLabel}>Voice Activity Detection</Text>
                <Text style={styles.settingDescription}>
                  Automatically detect when you start speaking
                </Text>
              </View>
              <Switch
                value={settings.vadEnabled || false}
                onValueChange={(value) => updateSetting('vadEnabled', value)}
                trackColor={{ false: '#D1D5DB', true: '#93C5FD' }}
                thumbColor={settings.vadEnabled ? '#3B82F6' : '#9CA3AF'}
              />
            </View>
          </View>

          {/* Auto Recording */}
          <View style={styles.settingItem}>
            <View style={styles.switchRow}>
              <View style={styles.switchInfo}>
                <Text style={styles.settingLabel}>Auto Recording</Text>
                <Text style={styles.settingDescription}>
                  Start recording automatically after TTS finishes
                </Text>
              </View>
              <Switch
                value={settings.autoRecord || false}
                onValueChange={(value) => updateSetting('autoRecord', value)}
                trackColor={{ false: '#D1D5DB', true: '#93C5FD' }}
                thumbColor={settings.autoRecord ? '#3B82F6' : '#9CA3AF'}
              />
            </View>
          </View>
        </View>
      )}
    </View>
  );

  const renderTTSSection = () => (
    <View style={styles.section}>
      {renderSectionHeader(
        'Text-to-Speech',
        'volume-high',
        'tts',
        'Speech output settings'
      )}

      {expandedSections.tts && (
        <View style={styles.sectionContent}>
          {/* Enable TTS */}
          <View style={styles.settingItem}>
            <View style={styles.switchRow}>
              <View style={styles.switchInfo}>
                <Text style={styles.settingLabel}>Enable TTS</Text>
                <Text style={styles.settingDescription}>
                  Convert assistant responses to speech
                </Text>
              </View>
              <Switch
                value={settings.ttsEnabled || false}
                onValueChange={(value) => updateSetting('ttsEnabled', value)}
                trackColor={{ false: '#D1D5DB', true: '#93C5FD' }}
                thumbColor={settings.ttsEnabled ? '#3B82F6' : '#9CA3AF'}
              />
            </View>
          </View>

          {/* Auto-play TTS */}
          <View style={[styles.settingItem, !settings.ttsEnabled && styles.disabled]}>
            <View style={styles.switchRow}>
              <View style={styles.switchInfo}>
                <Text style={styles.settingLabel}>Auto-play TTS</Text>
                <Text style={styles.settingDescription}>
                  Automatically play TTS for new responses
                </Text>
              </View>
              <Switch
                value={settings.ttsAutoPlay || false}
                onValueChange={(value) => updateSetting('ttsAutoPlay', value)}
                disabled={!settings.ttsEnabled}
                trackColor={{ false: '#D1D5DB', true: '#93C5FD' }}
                thumbColor={
                  settings.ttsAutoPlay && settings.ttsEnabled ? '#3B82F6' : '#9CA3AF'
                }
              />
            </View>
          </View>

          {/* TTS Speed */}
          <View style={[styles.settingItem, !settings.ttsEnabled && styles.disabled]}>
            <View style={styles.sliderHeader}>
              <Text style={styles.settingLabel}>Speech Speed</Text>
              <View style={styles.sliderValue}>
                <Text style={styles.sliderValueText}>
                  {((settings.ttsSpeed || 1.0) * 100).toFixed(0)}%
                </Text>
              </View>
            </View>
            <Slider
              style={styles.slider}
              value={settings.ttsSpeed || 1.0}
              onValueChange={(value) => updateSetting('ttsSpeed', value)}
              minimumValue={0.5}
              maximumValue={2.0}
              step={0.1}
              minimumTrackTintColor={settings.ttsEnabled ? '#3B82F6' : '#9CA3AF'}
              maximumTrackTintColor="#E5E7EB"
              thumbStyle={styles.sliderThumb}
              disabled={!settings.ttsEnabled}
            />
          </View>
        </View>
      )}
    </View>
  );

  const renderAdvancedSection = () => (
    <View style={styles.section}>
      {renderSectionHeader(
        'Advanced Settings',
        'construct',
        'advanced',
        'Performance and debugging options'
      )}

      {expandedSections.advanced && (
        <View style={styles.sectionContent}>
          {/* Streaming */}
          <View style={styles.settingItem}>
            <View style={styles.switchRow}>
              <View style={styles.switchInfo}>
                <Text style={styles.settingLabel}>Enable Streaming</Text>
                <Text style={styles.settingDescription}>
                  Stream responses in real-time as they are generated
                </Text>
              </View>
              <Switch
                value={settings.streamingEnabled || false}
                onValueChange={(value) => updateSetting('streamingEnabled', value)}
                trackColor={{ false: '#D1D5DB', true: '#93C5FD' }}
                thumbColor={settings.streamingEnabled ? '#3B82F6' : '#9CA3AF'}
              />
            </View>
          </View>

          {/* Debug Mode */}
          <View style={styles.settingItem}>
            <View style={styles.switchRow}>
              <View style={styles.switchInfo}>
                <Text style={styles.settingLabel}>Debug Mode</Text>
                <Text style={styles.settingDescription}>
                  Show detailed logs and performance metrics
                </Text>
              </View>
              <Switch
                value={settings.debugMode || false}
                onValueChange={(value) => updateSetting('debugMode', value)}
                trackColor={{ false: '#D1D5DB', true: '#93C5FD' }}
                thumbColor={settings.debugMode ? '#3B82F6' : '#9CA3AF'}
              />
            </View>
          </View>

          {/* Audio Quality */}
          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Audio Quality</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={settings.audioQuality || 'standard'}
                onValueChange={(quality) => updateSetting('audioQuality', quality)}
                style={styles.picker}
                itemStyle={styles.pickerItem}
              >
                <Picker.Item label="Low (8kHz)" value="low" />
                <Picker.Item label="Standard (16kHz)" value="standard" />
                <Picker.Item label="High (44.1kHz)" value="high" />
              </Picker>
            </View>
          </View>
        </View>
      )}
    </View>
  );

  if (!isVisible) return null;

  return (
    <Modal
      visible={isVisible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={handleCancel}
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={handleCancel}
          >
            <Text style={styles.headerButtonText}>Cancel</Text>
          </TouchableOpacity>

          <Text style={styles.headerTitle}>Voice Settings</Text>

          <TouchableOpacity
            style={[styles.headerButton, styles.saveButton]}
            onPress={handleSave}
          >
            <Text style={styles.saveButtonText}>Save</Text>
          </TouchableOpacity>
        </View>

        {/* Content */}
        <ScrollView
          style={styles.scrollView}
          showsVerticalScrollIndicator={false}
        >
          {renderModelSection()}
          {renderVoiceSection()}
          {renderTTSSection()}
          {renderAdvancedSection()}

          {/* Footer spacing */}
          <View style={styles.footer} />
        </ScrollView>

        {/* Loading Overlay */}
        {isLoading && (
          <View style={styles.loadingOverlay}>
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#3B82F6" />
              <Text style={styles.loadingText}>Saving settings...</Text>
            </View>
          </View>
        )}
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    ...Platform.select({
      ios: {
        paddingTop: 60,
      },
    }),
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
  },
  headerButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  saveButton: {
    backgroundColor: '#3B82F6',
  },
  headerButtonText: {
    fontSize: 16,
    color: '#6B7280',
  },
  saveButtonText: {
    fontSize: 16,
    color: 'white',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    backgroundColor: 'white',
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 12,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 3,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: '#FAFBFC',
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  sectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  sectionHeaderText: {
    marginLeft: 12,
    flex: 1,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
  },
  sectionSubtitle: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  sectionContent: {
    padding: 16,
  },
  settingItem: {
    marginBottom: 20,
  },
  settingHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1F2937',
  },
  settingDescription: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
    lineHeight: 16,
  },
  connectionBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    gap: 4,
  },
  connectionStatus: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  connectionBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#166534',
  },
  pickerContainer: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    marginTop: 8,
    overflow: 'hidden',
  },
  picker: {
    height: 50,
  },
  pickerItem: {
    fontSize: 16,
    color: '#1F2937',
  },
  connectionDetails: {
    marginTop: 8,
    padding: 12,
    backgroundColor: '#F3F4F6',
    borderRadius: 6,
  },
  connectionDetailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  connectionDetailText: {
    fontSize: 13,
    color: '#6B7280',
    textTransform: 'capitalize',
  },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  switchInfo: {
    flex: 1,
    marginRight: 16,
  },
  sliderHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  sliderValue: {
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  sliderValueText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#3B82F6',
  },
  slider: {
    width: '100%',
    height: 40,
  },
  sliderThumb: {
    backgroundColor: '#3B82F6',
    width: 20,
    height: 20,
  },
  disabled: {
    opacity: 0.5,
  },
  footer: {
    height: 40,
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingContainer: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    color: '#6B7280',
  },
});
