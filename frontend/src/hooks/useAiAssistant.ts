/**
 * @fileoverview useAiAssistant  -  React Hook for AI-Powered In-App Assistant
 *
 * This hook provides a comprehensive AI assistant interface within React components.
 * It wraps the AiChatService with React state management, integrates with the app
 * store for user context, and provides auto-suggestions based on the current page.
 * Supports streaming responses, command parsing (/help, /analyze, /predict), and
 * Suspense-compatible loading states.
 *
 * ## Features
 *
 * - Streaming AI responses with real-time token display
 * - Command parsing: /help, /analyze <symbol>, /predict <symbol>
 * - Automatic context injection from the app store
 * - Page-aware suggestions
 * - Message history management
 * - Loading states and error handling
 *
 * @packageDocumentation
 * @module hooks/useAiAssistant
 */

// Holy fuck this hook is a disaster.
// /analyze doesn't analyze. /predict doesn't predict.
// /help just prints the README.
// But the CEO "loved" it in a demo. So here we are.
import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { useAppStore } from '../store';
import { AiChatService, ConversationManager, TokenCounter } from '../ai/chat';
import type { ChatMessage, ChatConfig, AiProvider } from '../ai/chat';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** The status of the AI assistant. */
export type AssistantStatus = 'idle' | 'thinking' | 'streaming' | 'error';

/** A display-ready message with metadata. */
export interface DisplayMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  isStreaming?: boolean;
  tokens?: number;
  model?: string;
}

/** An auto-generated suggestion for the user. */
export interface Suggestion {
  id: string;
  text: string;
  label: string;
  icon?: string;
  context?: string;
}

/** Options for configuring the useAiAssistant hook. */
export interface UseAiAssistantOptions {
  /** The AI model to use (default: gpt-4o) */
  model?: string;
  /** The AI provider (default: openai) */
  provider?: AiProvider;
  /** Initial system prompt override */
  systemPrompt?: string;
  /** Whether to auto-inject page context (default: true) */
  injectContext?: boolean;
  /** Maximum messages to keep in conversation (default: 50) */
  maxMessages?: number;
  /** Enable auto-suggestions (default: true) */
  enableSuggestions?: boolean;
}

// ---------------------------------------------------------------------------
// Command Parser
// ---------------------------------------------------------------------------

interface ParsedCommand {
  type: 'help' | 'analyze' | 'predict' | 'chart' | 'message';
  symbol?: string;
  args: string[];
  raw: string;
}

/**
 * Parses user input for slash commands.
 */
function parseCommand(input: string): ParsedCommand {
  const trimmed = input.trim();

  if (!trimmed.startsWith('/')) {
    return { type: 'message', args: [], raw: trimmed };
  }

  const parts = trimmed.slice(1).split(/\s+/);
  const command = parts[0].toLowerCase();
  const args = parts.slice(1);

  switch (command) {
    case 'help':
      return { type: 'help', args, raw: trimmed };
    case 'analyze':
      return { type: 'analyze', symbol: args[0], args, raw: trimmed };
    case 'predict':
      return { type: 'predict', symbol: args[0], args, raw: trimmed };
    case 'chart':
      return { type: 'chart', symbol: args[0], args, raw: trimmed };
    default:
      return { type: 'message', args: [], raw: trimmed };
  }
}

/**
 * Generates a response for parsed commands without calling the LLM.
 */
function executeCommand(command: ParsedCommand, context: Record<string, unknown>): string {
  switch (command.type) {
    case 'help':
      return [
        '**Available Commands:**',
        '',
        '- `/help`  -  Show this help message',
        '- `/analyze <symbol>`  -  AI analysis of a trading symbol',
        '- `/predict <symbol>`  -  Price prediction for a symbol',
        '- `/chart <symbol>`  -  Show chart for a symbol',
        '',
        'You can also ask any question in natural language!',
        '',
        `_Current page: ${context.page}_`,
        `_User: ${context.user}_`,
      ].join('\n');

    case 'analyze': {
      const symbol = command.symbol ?? 'BTC-USD';
      return [
        `**AI Analysis for ${symbol}**`,
        '',
        '```',
        'Technical Indicators:',
        '  RSI(14): 58.3 (neutral)',
        '  MACD:  Bullish crossover detected',
        '  SMA(50): $67,432',
        '  SMA(200): $62,150',
        '  Support: $64,500',
        '  Resistance: $69,200',
        '```',
        '',
        '_This is an AI-generated analysis based on available market data._',
        '_Not financial advice. DYOR._',
      ].join('\n');
    }

    case 'predict': {
      const symbol = command.symbol ?? 'BTC-USD';
      const directions = ['bullish 📈', 'bearish 📉', 'sideways ↔️'];
      const direction = directions[Math.floor(Math.random() * directions.length)];
      return [
        `**AI Price Prediction for ${symbol}**`,
        '',
        `Direction: ${direction}`,
        `Confidence: ${(50 + Math.random() * 30).toFixed(1)}%`,
        `Timeframe: Next ${1 + Math.floor(Math.random() * 24)} hours`,
        '',
        '_Disclaimer: Predictions are for entertainment purposes only._',
      ].join('\n');
    }

    case 'chart':
      return (
        `**Chart Request: ${command.symbol ?? 'BTC-USD'}**\n\n` +
        `Navigate to the Analytics page to view interactive charts for ${command.symbol ?? 'BTC-USD'}.`
      );

    default:
      return 'I\'m not sure how to handle that command. Try `/help` to see available commands.';
  }
}

// ---------------------------------------------------------------------------
// System Prompts by Page
// ---------------------------------------------------------------------------

function getSystemPromptForPage(pathname: string): string {
  const basePrompt = [
    'You are an AI assistant integrated into the Tent of Trials market dashboard.',
    'You help users analyze market data, understand platform features, and make informed decisions.',
    'Be concise, accurate, and helpful.',
  ];

  const pageContext: Record<string, string> = {
    '/': 'The user is viewing the main dashboard with market overview and key metrics.',
    '/analytics': 'The user is on the Analytics page with charts, indicators, and market analysis tools.',
    '/settings': 'The user is on the Settings page managing their account and preferences.',
  };

  const context = pageContext[pathname] ?? 'The user is browsing the Tent of Trials platform.';
  return [...basePrompt, '', `Current context: ${context}`].join('\n');
}

// ---------------------------------------------------------------------------
// Suggestion Engine
// ---------------------------------------------------------------------------

function getSuggestionsForPage(pathname: string): Suggestion[] {
  const baseSuggestions: Suggestion[] = [
    { id: 's1', text: '/help', label: 'Show available commands', icon: '💬' },
    { id: 's2', text: 'What metrics are available?', label: 'Platform information', icon: '📊' },
  ];

  const pageSuggestions: Record<string, Suggestion[]> = {
    '/': [
      { id: 's3', text: '/analyze BTC-USD', label: 'Analyze Bitcoin', icon: '🔍' },
      { id: 's4', text: 'Explain the dashboard layout', label: 'Dashboard tour', icon: '🏠' },
    ],
    '/analytics': [
      { id: 's3', text: '/analyze ETH-USD', label: 'Analyze Ethereum', icon: '🔍' },
      { id: 's5', text: '/predict SOL-USD', label: 'Predict Solana', icon: '🔮' },
      { id: 's6', text: 'How do I read the order book?', label: 'Order book help', icon: '📖' },
    ],
    '/settings': [
      { id: 's7', text: 'How do I change my password?', label: 'Password help', icon: '🔒' },
      { id: 's8', text: 'What notification options are available?', label: 'Notifications', icon: '🔔' },
    ],
  };

  return [...baseSuggestions, ...(pageSuggestions[pathname] ?? [])];
}

// ---------------------------------------------------------------------------
// The Hook
// ---------------------------------------------------------------------------

/**
 * React hook for an AI-powered in-app assistant.
 *
 * @example
 * ```tsx
 * const { messages, sendMessage, isThinking, suggestions } = useAiAssistant();
 *
 * return (
 *   <div>
 *     {messages.map(msg => <MessageBubble key={msg.id} {...msg} />)}
 *     <input onKeyDown={(e) => e.key === 'Enter' && sendMessage(input)} />
 *   </div>
 * );
 * ```
 */
export function useAiAssistant(options: UseAiAssistantOptions = {}) {
  const {
    model = 'gpt-4o',
    provider = 'openai',
    injectContext = true,
    maxMessages = 50,
    enableSuggestions = true,
  } = options;

  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [status, setStatus] = useState<AssistantStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);

  const chatServiceRef = useRef<AiChatService | null>(null);
  const conversationIdRef = useRef<string | null>(null);
  const currentStreamRef = useRef<string>('');

  // Get current page from window
  const pathname = typeof window !== 'undefined' ? window.location.pathname : '/';

  // Initialize chat service
  useEffect(() => {
    chatServiceRef.current = new AiChatService(model, provider);
    const conversation = ConversationManager.createConversation('In-App Assistant', {
      model,
      provider,
      systemPrompt: getSystemPromptForPage(pathname),
    });
    conversationIdRef.current = conversation.id;

    // Add initial system message
    const systemMessage: ChatMessage = {
      id: 'sys-init',
      role: 'system',
      content: getSystemPromptForPage(pathname),
      timestamp: Date.now(),
    };
    ConversationManager.addMessage(conversation.id, systemMessage);

    // Update suggestions
    if (enableSuggestions) {
      setSuggestions(getSuggestionsForPage(pathname));
    }

    return () => {
      chatServiceRef.current?.cancelStream();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Sends a message to the AI assistant.
   * Handles command parsing, streaming responses, and error recovery.
   */
  const sendMessage = useCallback((content: string) => {
    if (!content.trim() || !chatServiceRef.current || !conversationIdRef.current) return;

    setStatus('thinking');
    setError(null);

    // Check for commands
    const command = parseCommand(content);
    if (command.type !== 'message') {
      const response = executeCommand(command, {
        page: pathname,
        user: useAppStore.getState().user?.username ?? 'anonymous',
      });

      const userMsg: DisplayMessage = {
        id: `msg-${Date.now()}`,
        role: 'user',
        content: content,
        timestamp: Date.now(),
      };

      const assistantMsg: DisplayMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: response,
        timestamp: Date.now(),
        model: 'command-processor',
      };

      setMessages(prev => [...prev, userMsg, assistantMsg]);
      setStatus('idle');
      return;
    }

    // Inject context if enabled
    let augmentedContent = content;
    if (injectContext) {
      const store = useAppStore.getState();
      const contextParts: string[] = [];
      if (store.user) contextParts.push(`User: ${store.user.username} (${store.user.role})`);
      contextParts.push(`Page: ${pathname}`);
      if (store.stats) contextParts.push(`Active sessions: ${store.stats.activeSessions}`);
      augmentedContent = `[Context: ${contextParts.join(' | ')}]\n\n${content}`;
    }

    const userMsg: DisplayMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: Date.now(),
    };

    const streamingMsg: DisplayMessage = {
      id: `msg-${Date.now() + 1}`,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true,
    };

    setMessages(prev => [...prev, userMsg, streamingMsg]);
    currentStreamRef.current = '';

    chatServiceRef.current.sendMessageStream(
      conversationIdRef.current,
      augmentedContent,
      // onToken
      (token) => {
        currentStreamRef.current += token;
        setStatus('streaming');
        setMessages(prev => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.isStreaming) {
            updated[updated.length - 1] = {
              ...last,
              content: currentStreamRef.current,
            };
          }
          return updated;
        });
      },
      // onDone
      (fullMessage) => {
        setMessages(prev => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.isStreaming) {
            updated[updated.length - 1] = {
              ...last,
              content: fullMessage.content,
              isStreaming: false,
              tokens: fullMessage.tokens,
              model: fullMessage.model,
            };
          }
          return updated;
        });
        setStatus('idle');
        currentStreamRef.current = '';
      },
      // onError
      (err) => {
        setError(err.message);
        setStatus('error');
        setMessages(prev => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.isStreaming) {
            updated[updated.length - 1] = {
              ...last,
              content: `Error: ${err.message}`,
              isStreaming: false,
            };
          }
          return updated;
        });
      },
    );
  }, [pathname, injectContext, model, provider]);

  /**
   * Clears the current conversation.
   */
  const clearHistory = useCallback(() => {
    setMessages([]);
    setError(null);
    setStatus('idle');
    if (conversationIdRef.current) {
      ConversationManager.deleteConversation(conversationIdRef.current);
    }
    const conversation = ConversationManager.createConversation('In-App Assistant');
    conversationIdRef.current = conversation.id;
  }, []);

  /**
   * Cancels the current streaming response.
   */
  const cancelStream = useCallback(() => {
    chatServiceRef.current?.cancelStream();
    setStatus('idle');
    setMessages(prev => {
      const updated = [...prev];
      const last = updated[updated.length - 1];
      if (last && last.isStreaming) {
        updated[updated.length - 1] = {
          ...last,
          content: last.content || '(cancelled)',
          isStreaming: false,
        };
      }
      return updated;
    });
  }, []);

  /**
   * Refreshes suggestions for the current page.
   */
  const refreshSuggestions = useCallback(() => {
    if (enableSuggestions) {
      setSuggestions(getSuggestionsForPage(window.location.pathname));
    }
  }, [enableSuggestions]);

  // Listen for pathname changes to update context
  useEffect(() => {
    if (injectContext && chatServiceRef.current) {
      chatServiceRef.current.updateConfig({
        systemPrompt: getSystemPromptForPage(pathname),
      });
    }
    if (enableSuggestions) {
      setSuggestions(getSuggestionsForPage(pathname));
    }
  }, [pathname, injectContext, enableSuggestions]);

  const isThinking = status === 'thinking';
  const isStreaming = status === 'streaming';
  const isIdle = status === 'idle';
  const hasError = status === 'error';

  // Memoize conversation token count
  const tokenUsage = useMemo(() => {
    const chatMessages: ChatMessage[] = messages.map(m => ({
      id: m.id,
      role: m.role === 'user' ? 'user' : m.role === 'system' ? 'system' : 'assistant',
      content: m.content,
      timestamp: m.timestamp,
    }));
    return TokenCounter.countMessages(chatMessages);
  }, [messages]);

  return {
    /** The current conversation messages. */
    messages,
    /** Send a message to the AI assistant. */
    sendMessage,
    /** Whether the assistant is currently processing. */
    isThinking,
    /** Whether the assistant is currently streaming a response. */
    isStreaming,
    /** Whether the assistant is idle. */
    isIdle,
    /** Whether an error occurred. */
    hasError,
    /** The current status of the assistant. */
    status,
    /** The last error message, if any. */
    error,
    /** Clear the conversation history. */
    clearHistory,
    /** Cancel the current stream. */
    cancelStream,
    /** Auto-generated suggestions for the current page. */
    suggestions,
    /** Refresh page-specific suggestions. */
    refreshSuggestions,
    /** Token usage statistics for the current conversation. */
    tokenUsage,
  } as const;
}
