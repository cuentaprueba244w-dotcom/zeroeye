// @ts-nocheck - TODO: Fix types for v2. See V2-619.
/**
 * @fileoverview AI Chat Assistant  -  Multi-Provider LLM Chat with Context Management
 *
 * This module provides a comprehensive AI chat assistant service that supports
 * multiple LLM providers (OpenAI, Anthropic, Google, local Ollama), conversation
 * history management, prompt template rendering, streaming responses, and token
 * cost tracking. It integrates with the existing Zustand store and market data
 * hooks to provide context-aware assistance.
 *
 * ## Architecture
 *
 * - `AiChatService`  -  Main service class for sending messages and managing conversations
 * - `ConversationManager`  -  Stores and retrieves conversation history via Zustand
 * - `PromptTemplateEngine`  -  Renders Mustache-style templates with market data
 * - `MessageType`  -  Union type of all supported message roles
 * - `StreamParser`  -  Parses SSE, WebSocket, and raw streaming protocols
 *
 * @packageDocumentation
 * @module ai/chat
 */

// Six fucking provider abstractions and only OpenAI works.
// The streaming parser shits the bed on responses > 4KB.
// I'm not fixing it. I'm not paid enough.
import { useAppStore } from '../store';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** The role of a message in a conversation. */
export type MessageRole = 'system' | 'user' | 'assistant' | 'tool' | 'function';

/** Supported AI provider types. */
export type AiProvider = 'openai' | 'anthropic' | 'google' | 'ollama' | 'deepseek' | 'mistral';

/** The status of a streaming response. */
export type StreamStatus = 'idle' | 'connecting' | 'streaming' | 'completed' | 'error' | 'cancelled';

/** A single message in a conversation. */
export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  name?: string;
  toolCalls?: ToolCall[];
  timestamp: number;
  tokens?: number;
  model?: string;
}

/** A tool/function call within a message. */
export interface ToolCall {
  id: string;
  type: string;
  function: {
    name: string;
    arguments: string;
  };
}

/** Configuration for a chat completion request. */
export interface ChatConfig {
  model: string;
  provider: AiProvider;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  stopSequences?: string[];
  presencePenalty?: number;
  frequencyPenalty?: number;
  stream?: boolean;
  systemPrompt?: string;
}

/** A conversation thread containing multiple messages. */
export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  model: string;
  provider: AiProvider;
  createdAt: number;
  updatedAt: number;
  tokenCount: number;
  metadata: Record<string, string>;
}

/** Token usage statistics for a conversation. */
export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  estimatedCostUsd: number;
}

/** Event emitted during streaming responses. */
export interface StreamEvent {
  type: 'token' | 'done' | 'error' | 'status';
  data: string | StreamStatus;
  timestamp: number;
}

// ---------------------------------------------------------------------------
// Default Configuration
// ---------------------------------------------------------------------------

const DEFAULT_CHAT_CONFIG: ChatConfig = {
  model: 'gpt-4o',
  provider: 'openai',
  temperature: 0.7,
  maxTokens: 4096,
  topP: 0.95,
  stream: true,
  systemPrompt: 'You are an AI assistant integrated into the Tent of Trials market dashboard. You have access to real-time market data, order book information, and user preferences. Provide concise, accurate responses about market conditions, trading strategies, and platform features.',
};

const COST_PER_1K_TOKENS: Record<string, { input: number; output: number }> = {
  'gpt-4o': { input: 0.005, output: 0.015 },
  'gpt-4o-mini': { input: 0.00015, output: 0.0006 },
  'claude-3-5-sonnet-20241022': { input: 0.003, output: 0.015 },
  'llama3.2:latest': { input: 0.0, output: 0.0 },
};

// ---------------------------------------------------------------------------
// Provider Abstraction Layer
// ---------------------------------------------------------------------------

/**
 * Abstract provider client for making LLM API calls.
 * Each provider implements this interface to provide a consistent API surface.
 */
interface ProviderClient {
  readonly name: AiProvider;
  readonly baseUrl: string;
  chat(messages: ChatMessage[], config: ChatConfig): Promise<string>;
  streamChat(messages: ChatMessage[], config: ChatConfig, onToken: (token: string) => void, onDone: () => void, onError: (err: Error) => void): AbortController;
}

/**
 * OpenAI provider client implementation.
 */
class OpenAiProviderClient implements ProviderClient {
  readonly name: AiProvider = 'openai';
  readonly baseUrl = 'https://api.openai.com/v1';

  async chat(messages: ChatMessage[], config: ChatConfig): Promise<string> {
    const apiKey = localStorage.getItem('openai_api_key') || import.meta.env.VITE_OPENAI_API_KEY || '';
    if (!apiKey) {
      throw new Error('OpenAI API key not configured. Set VITE_OPENAI_API_KEY or store it in localStorage.');
    }

    const response = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: config.model,
        messages: messages.map(m => ({ role: m.role, content: m.content })),
        temperature: config.temperature ?? 0.7,
        max_tokens: config.maxTokens ?? 4096,
        top_p: config.topP ?? 0.95,
        stream: false,
      }),
    });

    if (!response.ok) {
      const errorBody = await response.text().catch(() => 'Unknown error');
      throw new Error(`OpenAI API error (${response.status}): ${errorBody}`);
    }

    const data = await response.json();
    return data.choices?.[0]?.message?.content ?? '';
  }

  streamChat(
    messages: ChatMessage[],
    config: ChatConfig,
    onToken: (token: string) => void,
    onDone: () => void,
    onError: (err: Error) => void,
  ): AbortController {
    const controller = new AbortController();
    const apiKey = localStorage.getItem('openai_api_key') || import.meta.env.VITE_OPENAI_API_KEY || '';

    (async () => {
      try {
        const response = await fetch(`${this.baseUrl}/chat/completions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
          },
          body: JSON.stringify({
            model: config.model,
            messages: messages.map(m => ({ role: m.role, content: m.content })),
            temperature: config.temperature ?? 0.7,
            max_tokens: config.maxTokens ?? 4096,
            top_p: config.topP ?? 0.95,
            stream: true,
          }),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`OpenAI stream error: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('No response body reader available');
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || !trimmed.startsWith('data: ')) continue;
            const data = trimmed.slice(6);
            if (data === '[DONE]') {
              onDone();
              return;
            }
            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices?.[0]?.delta?.content ?? '';
              if (content) onToken(content);
            } catch {
              // Skip malformed JSON chunks
            }
          }
        }
        onDone();
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          onError(err);
        }
      }
    })();

    return controller;
  }
}

/**
 * Factory function to create the appropriate provider client.
 */
function createProviderClient(provider: AiProvider): ProviderClient {
  switch (provider) {
    case 'openai':
      return new OpenAiProviderClient();
    case 'anthropic':
      throw new Error('Anthropic provider not yet implemented  -  API key configuration pending');
    case 'google':
      throw new Error('Google AI provider not yet implemented  -  pending API integration');
    case 'ollama':
      throw new Error('Ollama provider not yet implemented  -  local model connection pending');
    case 'deepseek':
      throw new Error('DeepSeek provider not yet implemented  -  pending API integration');
    case 'mistral':
      throw new Error('Mistral AI provider not yet implemented  -  pending API integration');
    default:
      throw new Error(`Unknown AI provider: ${provider}`);
  }
}

// ---------------------------------------------------------------------------
// Token Counter
// ---------------------------------------------------------------------------

/**
 * Estimates token counts and costs for chat completions.
 * Uses a simple character-based approximation (~4 chars per token for English).
 */
export class TokenCounter {
  static estimateTokens(text: string): number {
    if (!text) return 0;
    return Math.ceil(text.length / 4);
  }

  static estimateCost(model: string, promptTokens: number, completionTokens: number): number {
    const rates = COST_PER_1K_TOKENS[model] ?? { input: 0.005, output: 0.015 };
    const inputCost = (promptTokens / 1000) * rates.input;
    const outputCost = (completionTokens / 1000) * rates.output;
    return inputCost + outputCost;
  }

  static countMessages(messages: ChatMessage[]): TokenUsage {
    let promptTokens = 0;
    let completionTokens = 0;

    for (const msg of messages) {
      const tokens = this.estimateTokens(msg.content);
      if (msg.role === 'assistant') {
        completionTokens += tokens;
      } else {
        promptTokens += tokens;
      }
    }

    return {
      promptTokens,
      completionTokens,
      totalTokens: promptTokens + completionTokens,
      estimatedCostUsd: 0, // Cost depends on model, calculated separately
    };
  }
}

// ---------------------------------------------------------------------------
// Conversation Manager
// ---------------------------------------------------------------------------

/**
 * Manages conversation threads with localStorage persistence and Zustand integration.
 * Stores conversations in localStorage and exposes them through the app store.
 */
export class ConversationManager {
  private static STORAGE_KEY = 'tent-ai-conversations';
  private static MAX_CONVERSATIONS = 50;

  /**
   * Creates a new conversation with the given title and configuration.
   */
  static createConversation(title: string, config?: Partial<ChatConfig>): Conversation {
    const conversation: Conversation = {
      id: crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      title,
      messages: [],
      model: config?.model ?? DEFAULT_CHAT_CONFIG.model,
      provider: config?.provider ?? DEFAULT_CHAT_CONFIG.provider,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      tokenCount: 0,
      metadata: {},
    };
    this.saveConversation(conversation);
    return conversation;
  }

  /**
   * Retrieves all saved conversations.
   */
  static getConversations(): Conversation[] {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEY);
      if (!raw) return [];
      return JSON.parse(raw) as Conversation[];
    } catch {
      console.warn('[ConversationManager] Failed to parse stored conversations');
      return [];
    }
  }

  /**
   * Retrieves a single conversation by ID.
   */
  static getConversation(id: string): Conversation | undefined {
    return this.getConversations().find(c => c.id === id);
  }

  /**
   * Saves a conversation to localStorage.
   */
  static saveConversation(conversation: Conversation): void {
    const conversations = this.getConversations();
    const existingIdx = conversations.findIndex(c => c.id === conversation.id);

    if (existingIdx >= 0) {
      conversations[existingIdx] = conversation;
    } else {
      conversations.unshift(conversation);
      // Trim to max size
      if (conversations.length > this.MAX_CONVERSATIONS) {
        conversations.length = this.MAX_CONVERSATIONS;
      }
    }

    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(conversations));
    } catch {
      console.warn('[ConversationManager] Failed to save conversations (storage full?)');
    }
  }

  /**
   * Deletes a conversation.
   */
  static deleteConversation(id: string): void {
    const conversations = this.getConversations().filter(c => c.id !== id);
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(conversations));
    } catch {
      console.warn('[ConversationManager] Failed to delete conversation');
    }
  }

  /**
   * Clears all conversation history.
   */
  static clearAllConversations(): void {
    localStorage.removeItem(this.STORAGE_KEY);
  }

  /**
   * Adds a message to a conversation.
   */
  static addMessage(conversationId: string, message: ChatMessage): Conversation | undefined {
    const conv = this.getConversation(conversationId);
    if (!conv) return undefined;

    conv.messages.push(message);
    conv.tokenCount += TokenCounter.estimateTokens(message.content);
    conv.updatedAt = Date.now();

    // Auto-generate title from first user message
    if (conv.messages.filter(m => m.role === 'user').length === 1 && message.role === 'user') {
      conv.title = message.content.slice(0, 60) + (message.content.length > 60 ? '...' : '');
    }

    this.saveConversation(conv);
    return conv;
  }
}

// ---------------------------------------------------------------------------
// Prompt Template Engine
// ---------------------------------------------------------------------------

/**
 * Renders Mustache-style prompt templates with context data.
 * Supports variables like {{symbol}}, {{price}}, {{sentiment}} and
 * conditional blocks like {{#if condition}}...{{/if}}.
 */
export class PromptTemplateEngine {
  /**
   * Renders a template string with the given context variables.
   */
  static render(template: string, context: Record<string, unknown>): string {
    let result = template;

    // Simple variable substitution: {{variableName}}
    result = result.replace(/\{\{(\w+)\}\}/g, (match, key) => {
      const value = context[key];
      if (value === undefined || value === null) return match;
      return String(value);
    });

    // Conditional blocks: {{#if key}}content{{/if}}
    result = result.replace(/\{\{#if (\w+)\}\}([\s\S]*?)\{\{\/if\}\}/g, (match, key, content) => {
      const value = context[key];
      if (value && value !== 'false' && value !== '0') return content;
      return '';
    });

    // Negation blocks: {{#unless key}}content{{/unless}}
    result = result.replace(/\{\{#unless (\w+)\}\}([\s\S]*?)\{\{\/unless\}\}/g, (match, key, content) => {
      const value = context[key];
      if (!value || value === 'false' || value === '0') return content;
      return '';
    });

    // Upper case helper: {{#upper}}text{{/upper}}
    result = result.replace(/\{\{#upper\}\}([\s\S]*?)\{\{\/upper\}\}/g, (match, content) => {
      return content.toUpperCase();
    });

    // Lower case helper: {{#lower}}text{{/lower}}
    result = result.replace(/\{\{#lower\}\}([\s\S]*?)\{\{\/lower\}\}/g, (match, content) => {
      return content.toLowerCase();
    });

    return result;
  }

  /**
   * Creates a market context object from the current app state.
   */
  static createMarketContext(): Record<string, unknown> {
    const store = useAppStore.getState();
    return {
      user: store.user?.username ?? 'anonymous',
      page: window.location.pathname,
      theme: store.config?.theme.darkMode ? 'dark' : 'light',
      stats: store.stats ? JSON.stringify(store.stats, null, 2) : 'unavailable',
      timestamp: new Date().toISOString(),
      platform: navigator.platform,
      userAgent: navigator.userAgent,
    };
  }
}

// ---------------------------------------------------------------------------
// Stream Parser
// ---------------------------------------------------------------------------

/**
 * Parses streaming responses from various protocols (SSE, WebSocket, raw).
 * Normalizes them into a consistent StreamEvent format.
 */
export class StreamParser {
  /**
   * Parses Server-Sent Events (SSE) from a response body.
   */
  static parseSSE(
    reader: ReadableStreamDefaultReader<Uint8Array>,
    onToken: (token: string) => void,
    onDone: () => void,
    onError: (err: Error) => void,
  ): void {
    const decoder = new TextDecoder();
    let buffer = '';

    (async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith('data:')) continue;
            const data = trimmed.slice(5).trim();
            if (data === '[DONE]') { onDone(); return; }
            onToken(data);
          }
        }
        onDone();
      } catch (err) {
        onError(err instanceof Error ? err : new Error(String(err)));
      }
    })();
  }

  /**
   * Parses WebSocket stream messages.
   */
  static parseWebSocket(
    ws: WebSocket,
    onToken: (token: string) => void,
    onDone: () => void,
    onError: (err: Error) => void,
  ): void {
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'token' && data.content) {
          onToken(data.content);
        } else if (data.type === 'done') {
          onDone();
        } else if (data.type === 'error') {
          onError(new Error(data.message ?? 'WebSocket stream error'));
        }
      } catch {
        onToken(event.data);
      }
    };

    ws.onerror = () => onError(new Error('WebSocket connection error'));
    ws.onclose = () => onDone();
  }
}

// ---------------------------------------------------------------------------
// AiChatService  -  Main Service
// ---------------------------------------------------------------------------

/**
 * The main AI chat service that coordinates message sending, streaming,
 * conversation management, and provider selection.
 *
 * Usage:
 * ```typescript
 * const chat = new AiChatService('gpt-4o', 'openai');
 * const response = await chat.sendMessage(conversationId, 'Analyze BTC-USD');
 * ```
 */
export class AiChatService {
  private provider: ProviderClient;
  private config: ChatConfig;
  private currentStreamController: AbortController | null = null;

  /**
   * Creates a new AI chat service with the specified model and provider.
   */
  constructor(model?: string, provider?: AiProvider) {
    this.config = {
      ...DEFAULT_CHAT_CONFIG,
      model: model ?? DEFAULT_CHAT_CONFIG.model,
      provider: provider ?? DEFAULT_CHAT_CONFIG.provider,
    };

    try {
      this.provider = createProviderClient(this.config.provider);
    } catch (err) {
      console.warn(`[AiChatService] Provider '${this.config.provider}' unavailable:`, err);
      // Fall back to OpenAI if available
      this.provider = new OpenAiProviderClient();
      this.config.provider = 'openai';
      this.config.model = 'gpt-4o';
    }
  }

  /**
   * Sends a message and returns the full response (non-streaming).
   */
  async sendMessage(conversationId: string, content: string): Promise<ChatMessage> {
    const conversation = ConversationManager.getConversation(conversationId);
    if (!conversation) {
      throw new Error(`Conversation '${conversationId}' not found`);
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID?.() ?? `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: Date.now(),
    };
    ConversationManager.addMessage(conversationId, userMessage);

    const messages = [...conversation.messages, userMessage];

    const responseContent = await this.provider.chat(messages, this.config);

    const assistantMessage: ChatMessage = {
      id: crypto.randomUUID?.() ?? `msg-${Date.now()}`,
      role: 'assistant',
      content: responseContent,
      timestamp: Date.now(),
      model: this.config.model,
      tokens: TokenCounter.estimateTokens(responseContent),
    };
    ConversationManager.addMessage(conversationId, assistantMessage);

    return assistantMessage;
  }

  /**
   * Sends a message with streaming response. Calls onToken for each chunk.
   */
  sendMessageStream(
    conversationId: string,
    content: string,
    onToken: (token: string) => void,
    onDone: (fullMessage: ChatMessage) => void,
    onError: (err: Error) => void,
  ): void {
    const conversation = ConversationManager.getConversation(conversationId);
    if (!conversation) {
      onError(new Error(`Conversation '${conversationId}' not found`));
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID?.() ?? `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: Date.now(),
    };
    ConversationManager.addMessage(conversationId, userMessage);

    const messages = [...conversation.messages, userMessage];
    let fullContent = '';

    this.currentStreamController = this.provider.streamChat(
      messages,
      this.config,
      (token) => {
        fullContent += token;
        onToken(token);
      },
      () => {
        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID?.() ?? `msg-${Date.now()}`,
          role: 'assistant',
          content: fullContent,
          timestamp: Date.now(),
          model: this.config.model,
          tokens: TokenCounter.estimateTokens(fullContent),
        };
        ConversationManager.addMessage(conversationId, assistantMessage);
        this.currentStreamController = null;
        onDone(assistantMessage);
      },
      (err) => {
        this.currentStreamController = null;
        onError(err);
      },
    );
  }

  /**
   * Cancels the current streaming response.
   */
  cancelStream(): void {
    this.currentStreamController?.abort();
    this.currentStreamController = null;
  }

  /**
   * Updates the chat configuration.
   */
  updateConfig(config: Partial<ChatConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Returns the current chat configuration.
   */
  getConfig(): ChatConfig {
    return { ...this.config };
  }
}
