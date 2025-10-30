import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  ReactNode,
} from 'react';
import axios from 'axios';
import type {Node, Relationship} from '@neo4j-nvl/base';

export type ChatMessage = {
  id: number | string;
  user: string;
  message: string;
  datetime: string;
  isTyping?: boolean;
  src?: Array<string>;
  nodes?: Node[];
  rels?: Relationship[];
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
  isHistoryReady: boolean;
};

const ChatSessionContext = createContext<ChatSessionContextValue | undefined>(undefined);

const STORAGE_KEY = 'drchat-chat-sessions';
const CHAT_HISTORY_SERVICE_URL = import.meta.env.VITE_CHAT_HISTORY_SERVICE_URL;
const CHAT_HISTORY_BASE_URL = CHAT_HISTORY_SERVICE_URL
  ? CHAT_HISTORY_SERVICE_URL.replace(/\/$/, '')
  : undefined;

type StoredUser = {
  id?: string;
  email?: string;
  name?: string;
  token?: string;
};

type BackendMessage = {
  content: string;
  role: string;
  created_at?: string;
};

type BackendSession = {
  session_id: string;
  session_name: string;
  session_created_at?: string;
  messages?: BackendMessage[];
};

type BackendSessionsResponse = {
  sessions?: BackendSession[];
};

const generateSessionId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }

  return Math.random().toString(36).slice(2, 11);
};

const safeDate = (value?: string) => {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return parsed;
};

const isoOrNow = (value?: string) => {
  const date = safeDate(value);
  return (date ?? new Date()).toISOString();
};

const displayFromIso = (value?: string) => {
  const date = safeDate(value) ?? new Date();
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
};

const mapBackendSession = (session: BackendSession): ChatSession => {
  const createdAtIso = isoOrNow(session.session_created_at);
  const apiMessages = session.messages ?? [];

  const messages: ChatMessage[] = apiMessages.map((message, index) => {
    const createdIso = isoOrNow(message.created_at);
    return {
      id: `${session.session_id}-${index}-${createdIso}`,
      user: message.role === 'ai' ? 'chatbot' : 'user',
      message: message.content,
      datetime: displayFromIso(message.created_at),
    };
  });

  const lastMessageIso = apiMessages.length
    ? isoOrNow(apiMessages[apiMessages.length - 1]?.created_at)
    : createdAtIso;

  return {
    id: session.session_id,
    title: session.session_name || 'New chat',
    createdAt: createdAtIso,
    updatedAt: lastMessageIso,
    messages,
  };
};

const mapBackendSessions = (payload: BackendSessionsResponse | null | undefined): ChatSession[] => {
  if (!payload?.sessions || payload.sessions.length === 0) {
    return [];
  }

  return payload.sessions.map(mapBackendSession);
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

const resolveUserId = (): string | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const stored = window.localStorage.getItem('user');
    if (!stored) {
      return null;
    }

    const parsed = JSON.parse(stored) as StoredUser;
    return parsed?.id ?? parsed?.email ?? null;
  } catch (error) {
    console.error('Unable to read user information from storage', error);
    return null;
  }
};

export function ChatSessionProvider({ children }: { children: ReactNode }) {
  const initialSessions = useMemo(() => loadSessions(), []);
  const [sessions, setSessions] = useState<ChatSession[]>(initialSessions);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(
    initialSessions.length > 0 ? initialSessions[0].id : null
  );
  const [userId, setUserId] = useState<string | null>(null);
  const [isUserIdResolved, setIsUserIdResolved] = useState(false);
  const [hasAttemptedHistorySync, setHasAttemptedHistorySync] = useState(!CHAT_HISTORY_BASE_URL);

  useEffect(() => {
    setUserId(resolveUserId());
    setIsUserIdResolved(true);
  }, []);

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

  useEffect(() => {
    if (!CHAT_HISTORY_BASE_URL) {
      setHasAttemptedHistorySync(true);
      return;
    }

    if (!isUserIdResolved) {
      return;
    }

    if (!userId) {
      setHasAttemptedHistorySync(true);
      return;
    }

    let isCancelled = false;

    const fetchSessions = async () => {
      try {
        const { data } = await axios.get<BackendSessionsResponse>(
          `${CHAT_HISTORY_BASE_URL}/sessions`,
          {
            params: { user_id: userId },
          }
        );

        if (isCancelled) {
          return;
        }

        const mapped = mapBackendSessions(data);
        setSessions(mapped);
        setCurrentSessionId((prevCurrentId) => {
          if (prevCurrentId && mapped.some((session) => session.id === prevCurrentId)) {
            return prevCurrentId;
          }
          return mapped[0]?.id ?? null;
        });
      } catch (error) {
        if (!isCancelled) {
          console.error('Unable to load chat sessions from history service', error);
        }
      } finally {
        if (!isCancelled) {
          setHasAttemptedHistorySync(true);
        }
      }
    };

    void fetchSessions();

    return () => {
      isCancelled = true;
    };
  }, [userId, isUserIdResolved, CHAT_HISTORY_BASE_URL]);

  const currentSession = useMemo(() => {
    if (!currentSessionId) {
      return null;
    }

    return sessions.find((session) => session.id === currentSessionId) ?? null;
  }, [currentSessionId, sessions]);

  const createNewSession = useCallback(
    (title = 'New chat') => {
      const now = new Date().toISOString();
      const sessionId = generateSessionId();
      const newSession: ChatSession = {
        id: sessionId,
        title,
        createdAt: now,
        updatedAt: now,
        messages: [],
      };

      setSessions((prev) => [newSession, ...prev]);
      setCurrentSessionId(sessionId);

      if (CHAT_HISTORY_BASE_URL && userId) {
        void axios
          .post(`${CHAT_HISTORY_BASE_URL}/session`, {
            user_id: userId,
            session_id: sessionId,
            session_name: title,
          })
          .then((response) => {
            const createdAt = isoOrNow(response.data?.created_at);
            setSessions((prev) =>
              prev.map((session) => {
                if (session.id === sessionId) {
                  return {
                    ...session,
                    createdAt,
                    updatedAt: createdAt,
                  };
                }
                return session;
              })
            );
          })
          .catch((error) => {
            console.error('Unable to persist chat session in history service', error);
          });
      }
    },
    [userId, CHAT_HISTORY_BASE_URL]
  );

  const switchSession = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId);
  }, []);

  const deleteSession = useCallback(
    (sessionId: string) => {
      setSessions((prev) => {
        const filtered = prev.filter((session) => session.id !== sessionId);
        if (filtered.length !== prev.length) {
          setCurrentSessionId((prevCurrentId) => {
            if (prevCurrentId === sessionId) {
              return filtered[0]?.id ?? null;
            }
            return prevCurrentId;
          });
        }
        return filtered;
      });

      if (CHAT_HISTORY_BASE_URL && userId) {
        void axios
          .delete(`${CHAT_HISTORY_BASE_URL}/session`, {
            data: {
              user_id: userId,
              session_id: sessionId,
            },
          })
          .catch((error) => {
            console.error('Unable to delete chat session in history service', error);
          });
      }
    },
    [userId, CHAT_HISTORY_BASE_URL]
  );

  const addMessageToCurrentSession = useCallback(
    (message: ChatMessage) => {
      if (!currentSessionId) {
        const now = new Date().toISOString();
        const sessionId = generateSessionId();
        const newSession: ChatSession = {
          id: sessionId,
          title: 'New chat',
          createdAt: now,
          updatedAt: now,
          messages: [message],
        };
        setSessions((prev) => [newSession, ...prev]);
        setCurrentSessionId(sessionId);

        if (CHAT_HISTORY_BASE_URL && userId) {
          void axios
            .post(`${CHAT_HISTORY_BASE_URL}/session`, {
              user_id: userId,
              session_id: sessionId,
              session_name: 'New chat',
            })
            .then((response) => {
              const createdAt = isoOrNow(response.data?.created_at);
              setSessions((prev) =>
                prev.map((session) => {
                  if (session.id === sessionId) {
                    return {
                      ...session,
                      createdAt,
                      updatedAt: createdAt,
                    };
                  }
                  return session;
                })
              );
            })
            .catch((error) => {
              console.error('Unable to persist chat session created from message', error);
            });
        }
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
    [currentSessionId, userId, CHAT_HISTORY_BASE_URL]
  );

  const updateSessionTitle = useCallback(
    (sessionId: string, title: string) => {
      setSessions((prev) =>
        prev.map((session) => {
          if (session.id === sessionId) {
            return {
              ...session,
              title,
              updatedAt: new Date().toISOString(),
            };
          }
          return session;
        })
      );

      if (CHAT_HISTORY_BASE_URL && userId) {
        void axios
          .put(`${CHAT_HISTORY_BASE_URL}/session`, {
            user_id: userId,
            session_id: sessionId,
            new_name: title,
          })
          .catch((error) => {
            console.error('Unable to update chat session in history service', error);
          });
      }
    },
    [userId, CHAT_HISTORY_BASE_URL]
  );

  const value = useMemo<ChatSessionContextValue>(
    () => ({
      sessions,
      currentSession,
      createNewSession,
      switchSession,
      deleteSession,
      addMessageToCurrentSession,
      updateSessionTitle,
      isHistoryReady: hasAttemptedHistorySync,
    }),
    [
      sessions,
      currentSession,
      createNewSession,
      switchSession,
      deleteSession,
      addMessageToCurrentSession,
      updateSessionTitle,
      hasAttemptedHistorySync,
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
