import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  ReactNode,
} from 'react';

export type ChatMessage = {
  id: number | string;
  user: string;
  message: string;
  datetime: string;
  isTyping?: boolean;
  src?: Array<string>;
};

export type ChatSession = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
};

export type ChatSessionContextValue = {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  createNewSession: (title?: string) => void;
  switchSession: (sessionId: string) => void;
  deleteSession: (sessionId: string) => void;
  addMessageToCurrentSession: (message: ChatMessage) => void;
  updateSessionTitle: (sessionId: string, title: string) => void;
};

const ChatSessionContext = createContext<ChatSessionContextValue | undefined>(undefined);

const STORAGE_KEY = 'drchat-chat-sessions';

const generateSessionId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }

  return Math.random().toString(36).slice(2, 11);
};

const loadSessions = (): ChatSession[] => {
  if (typeof window === 'undefined') {
    return [];
  }

  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      return [];
    }

    const parsed = JSON.parse(stored) as ChatSession[];
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed;
  } catch (error) {
    console.error('Unable to load chat sessions from storage', error);
    return [];
  }
};

export function ChatSessionProvider({ children }: { children: ReactNode }) {
  const initialSessions = useMemo(() => loadSessions(), []);
  const [sessions, setSessions] = useState<ChatSession[]>(initialSessions);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(
    initialSessions.length > 0 ? initialSessions[0].id : null
  );

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    } catch (error) {
      console.error('Unable to persist chat sessions', error);
    }
  }, [sessions]);

  const currentSession = useMemo(() => {
    if (!currentSessionId) {
      return null;
    }

    return sessions.find((session) => session.id === currentSessionId) ?? null;
  }, [currentSessionId, sessions]);

  const createNewSession = useCallback((title = 'New Chat') => {
    const now = new Date().toISOString();
    const newSession: ChatSession = {
      id: generateSessionId(),
      title,
      createdAt: now,
      updatedAt: now,
      messages: [],
    };

    setSessions((prev) => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
  }, []);

  const switchSession = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId);
  }, []);

  const deleteSession = useCallback(
    (sessionId: string) => {
      setSessions((prev) => prev.filter((session) => session.id !== sessionId));

      if (currentSessionId === sessionId) {
        const remaining = sessions.filter((session) => session.id !== sessionId);
        setCurrentSessionId(remaining[0]?.id ?? null);
      }
    },
    [currentSessionId, sessions]
  );

  const addMessageToCurrentSession = useCallback(
    (message: ChatMessage) => {
      if (!currentSessionId) {
        const now = new Date().toISOString();
        const newSession: ChatSession = {
          id: generateSessionId(),
          title: 'New Chat',
          createdAt: now,
          updatedAt: now,
          messages: [message],
        };
        setSessions((prev) => [newSession, ...prev]);
        setCurrentSessionId(newSession.id);
        return;
      }

      setSessions((prev) =>
        prev.map((session) => {
          if (session.id !== currentSessionId) {
            return session;
          }

          return {
            ...session,
            messages: [...session.messages, message],
            updatedAt: new Date().toISOString(),
          };
        })
      );
    },
    [currentSessionId]
  );

  const updateSessionTitle = useCallback((sessionId: string, title: string) => {
    setSessions((prev) =>
      prev.map((session) =>
        session.id === sessionId
          ? {
              ...session,
              title,
              updatedAt: new Date().toISOString(),
            }
          : session
      )
    );
  }, []);

  const value = useMemo<ChatSessionContextValue>(
    () => ({
      sessions,
      currentSession,
      createNewSession,
      switchSession,
      deleteSession,
      addMessageToCurrentSession,
      updateSessionTitle,
    }),
    [
      sessions,
      currentSession,
      createNewSession,
      switchSession,
      deleteSession,
      addMessageToCurrentSession,
      updateSessionTitle,
    ]
  );

  return <ChatSessionContext.Provider value={value}>{children}</ChatSessionContext.Provider>;
}

export function useChatSession() {
  const context = useContext(ChatSessionContext);
  if (!context) {
    throw new Error('useChatSession must be used within a ChatSessionProvider');
  }

  return context;
}

export default ChatSessionProvider;
