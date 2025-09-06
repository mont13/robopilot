import axios from 'axios';
import { ConversationHistory, AgentExecutionRequest, AgentExecutionResponse, CreateSessionResponse } from '@/types/api';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'https://api.example.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getActiveSession = async (): Promise<ConversationHistory> => {
  try {
    const response = await api.get<ConversationHistory>('/api/agent/sessions/active');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch active session:', error);
    throw new Error('Failed to fetch conversation history');
  }
};

export const createNewSession = async (): Promise<CreateSessionResponse> => {
  try {
    const response = await api.post<CreateSessionResponse>('/api/agent/sessions');
    return response.data;
  } catch (error) {
    console.error('Failed to create new session:', error);
    throw new Error('Failed to create new session');
  }
};

export const sendChatMessage = async (request: AgentExecutionRequest): Promise<AgentExecutionResponse> => {
  try {
    const response = await api.post<AgentExecutionResponse>('/api/agent/chat', request);
    return response.data;
  } catch (error) {
    console.error('Failed to send chat message:', error);
    throw new Error('Failed to send message');
  }
};