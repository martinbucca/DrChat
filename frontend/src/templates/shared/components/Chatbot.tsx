/* eslint-disable no-confusing-arrow */
import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Button,
  Widget,
  Typography,
  Avatar,
  TextInput,
  IconButton,
  useCopyToClipboard,
  Modal,
  Drawer,
  LoadingSpinner,
  TextLink,
} from '@neo4j-ndl/react';

import ChatBotAvatar from '../assets/chatbot-ai.png';
import {
  ArrowPathIconOutline,
  ClipboardDocumentIconOutline,
  HandThumbDownIconOutline,
  InformationCircleIconOutline,
  SpeakerWaveIconOutline,
  PencilSquareIconOutline,
  ArrowUpTrayIconOutline,
  XMarkIconOutline,
  CheckIconOutline,
  TrashIconOutline,
  SidebarLineLeftIcon,
  ArrowRightIconOutline,
  ArrowLeftIconOutline,
  ChevronDownIconOutline,
  ChevronUpIconOutline,
  HandThumbUpIconOutline,
} from '@neo4j-ndl/react/icons';

import { PiGraphBold } from 'react-icons/pi';

import RetrievalInformation from './RetrievalInformation';
import { useChatSession, ChatMessage } from '../../../context/ChatSessionContext';
import axios from 'axios';

// ---------------------------------------------
// Types
// ---------------------------------------------

type ChatbotProps = {
  messages?: {
    id: number;
    user: string;
    message: string;
    datetime: string;
    isTyping?: boolean;
    src?: Array<string>;
  }[];
};

type ChatbotResponse = {
  response: string;
  src: string[];
  entities?: string[];
  model?: string;
  timeTaken?: number;
  createdAt?: string;
};

// Meta (entities/model/time) we store alongside each chatbot message id
type MsgMeta = { entities: string[]; model: string; timeTaken: number };

type UploadedFile = {
  id: string;
  name: string;
  status: string;
  uploadedAt: string;
  size: number;
};

// ---------------------------------------------
// Utils
// ---------------------------------------------
const formattedTextStyle = { color: 'rgb(var(--theme-palette-discovery-bg-strong))' } as const;

function toLocalISOString(date: Date) {
  const pad = (n: number, width = 2) => n.toString().padStart(width, '0');
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());
  const seconds = pad(date.getSeconds());
  const millis = pad(date.getMilliseconds(), 3);
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}.${millis}`;
}

// ---------------------------------------------
// Backend calls
// ---------------------------------------------
const CHAT_SERVICE_URL = import.meta.env.VITE_CHAT_SERVICE_URL;
const FILE_SERVICE_URL = import.meta.env.VITE_FILE_SERVICE_URL;

async function chatBotAPI(question: string, sessionId?: string, createdAt?: string) {
  console.log("Starting chat API call");
  console.log("Environment VITE_CHAT_SERVICE_URL:", import.meta.env.VITE_CHAT_SERVICE_URL);
  console.log("Final CHAT_SERVICE_URL:", CHAT_SERVICE_URL);
  
  if (!CHAT_SERVICE_URL) {
    console.log("No CHAT_SERVICE_URL configured, using fallback demo");
    // Fallback demo payload when no backend is configured
    const start = Date.now();
    await new Promise((r) => setTimeout(r, 1000));
    const end = Date.now();
    return {
      response: {
        answer:
          'Hello, here is an example response with sources. To use the chatbot, plug this to your backend with a fetch containing an object response of type: {response: string, src: Array<string>}'
      ,
        created_at: new Date().toISOString(),
        retriever_result: [
          { listIds: ['1:1234-abcd-efgh-ijkl-5678:2'] },
          { listIds: ['3:8765-zyxw-vuts-rqpo-4321:4'] },
        ],
      },
      timeTaken: end - start,
    } as const;
  }

  const startTime = Date.now();
  const payload = {
    query: question,
    session_id: sessionId,
    created_at: createdAt,
  };
  const url = `${CHAT_SERVICE_URL}/answer_question`;
  console.log("Making chat request to URL:", url);
  console.log("Chat payload:", payload);
  
  try {
    const { data } = await axios.post(url, payload);
    const endTime = Date.now();
    console.log("Chat response successful:", data);
    return { response: data, timeTaken: endTime - startTime };
  } catch (err) {
    console.error("Chat API error:", err);
    throw err;
  }
}

async function sendFeedback(messageId: number, like: boolean) {
  console.log("Sending feedback");
  console.log("CHAT_SERVICE_URL:", CHAT_SERVICE_URL);
  
  if (!CHAT_SERVICE_URL) {
    console.log("No CHAT_SERVICE_URL configured, skipping feedback");
    return;
  }
  
  const url = `${CHAT_SERVICE_URL}/feedback`;
  const payload = {
    message_id: messageId,
    like,
  };
  
  console.log("Sending feedback to URL:", url);
  console.log("Feedback payload:", payload);
  
  try {
    await axios.post(url, payload);
    console.log("Feedback sent successfully");
  } catch (e) {
    console.error('Error sending feedback:', e);
  }
}

// ---------------------------------------------
// Component
// ---------------------------------------------
export default function Chatbot(props: ChatbotProps) {
  const { messages = [] } = props;
  const {
    currentSession,
    sessions,
    createNewSession,
    switchSession,
    deleteSession,
    addMessageToCurrentSession,
    updateSessionTitle,
  } = useChatSession();

  const hasInitialized = useRef(false);

  useEffect(() => {
    if (sessions.length === 0 && !hasInitialized.current) {
      hasInitialized.current = true;
      if (messages.length > 0) {
        createNewSession('Sample Chat');
        messages.forEach((msg) => {
          addMessageToCurrentSession(msg as ChatMessage);
        });
      } else {
        createNewSession('New Chat');
      }
    }
  }, [sessions.length, messages, createNewSession, addMessageToCurrentSession]);

  const [inputMessage, setInputMessage] = useState('');
  const [, copy] = useCopyToClipboard();
  const [isOpenModal, setIsOpenModal] = useState<boolean>(false);
  const [timeTaken, setTimeTaken] = useState<number>(0);
  const [sourcesModal, setSourcesModal] = useState<string[]>([]);
  const [entitiesModal, setEntitiesModal] = useState<string[]>([]);
  const [modelModal, setModelModal] = useState<string>('');
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(true);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [isChatListOpen, setIsChatListOpen] = useState<boolean>(true);
  const [uploadedFilesBySession, setUploadedFilesBySession] = useState<Record<string, UploadedFile[]>>({});
  const [uploadErrorsBySession, setUploadErrorsBySession] = useState<Record<string, string | null>>({});
  const [uploadingSessionId, setUploadingSessionId] = useState<string | null>(null);
  const [expandedFilesSessions, setExpandedFilesSessions] = useState<Record<string, boolean>>({});

  const [typingMessageId, setTypingMessageId] = useState<number | null>(null);
  const [currentTypingText, setCurrentTypingText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingPlaying, setLoadingPlaying] = useState<boolean>(false);

  // messageId -> meta
  const messageMetaRef = useRef<Map<number, MsgMeta>>(new Map());
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleCloseModal = () => setIsOpenModal(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputMessage(e.target.value);
  };

  useEffect(() => {
    if (!currentSession) {
      return;
    }

    if (uploadedFilesBySession[currentSession.id] && expandedFilesSessions[currentSession.id] === undefined) {
      setExpandedFilesSessions((prev) => ({ ...prev, [currentSession.id]: true }));
    }
  }, [currentSession?.id, expandedFilesSessions, uploadedFilesBySession]);

  const handleFileInputChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';

    if (!file) {
      return;
    }

    if (!currentSession) {
      console.warn('Attempted to upload a file without an active chat session');
      return;
    }

    if (!FILE_SERVICE_URL) {
      setUploadErrorsBySession((prev) => ({ ...prev, [currentSession.id]: 'File service URL is not configured.' }));
      return;
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadErrorsBySession((prev) => ({ ...prev, [currentSession.id]: 'Solo se aceptan archivos PDF.' }));
      return;
    }

    try {
      setUploadErrorsBySession((prev) => ({ ...prev, [currentSession.id]: null }));
      setUploadingSessionId(currentSession.id);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', currentSession.id);

      const baseUrl = FILE_SERVICE_URL.replace(/\/$/, '');
      const { data } = await axios.post(`${baseUrl}/files/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const uploaded: UploadedFile = {
        id: data.file_id,
        name: data.original_filename,
        status: data.status,
        uploadedAt: data.upload_time,
        size: data.file_size,
      };

      setUploadedFilesBySession((prev) => {
        const existing = prev[currentSession.id] ?? [];
        return { ...prev, [currentSession.id]: [uploaded, ...existing] };
      });
      setExpandedFilesSessions((prev) => ({ ...prev, [currentSession.id]: true }));
    } catch (error) {
      console.error('File upload failed', error);
      if (axios.isAxiosError(error)) {
        const detail = (error.response?.data as { detail?: string })?.detail;
        setUploadErrorsBySession((prev) => ({
          ...prev,
          [currentSession.id]: detail || error.message || 'Error subiendo el archivo.',
        }));
      } else if (error instanceof Error) {
        setUploadErrorsBySession((prev) => ({ ...prev, [currentSession.id]: error.message }));
      } else {
        setUploadErrorsBySession((prev) => ({ ...prev, [currentSession.id]: 'Error subiendo el archivo.' }));
      }
      setExpandedFilesSessions((prev) => ({ ...prev, [currentSession.id]: true }));
    } finally {
      setUploadingSessionId((prev) => (prev === currentSession.id ? null : prev));
    }
  };

  // ---------- Audio (TTS) ----------
  const chatBotVoice = async (message: string) => {
    return new Promise<void>((resolve) => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(message);
        utterance.lang = 'en-US';
        utterance.rate = 1;
        utterance.pitch = 1;
        utterance.onend = () => resolve();
        utterance.onerror = () => resolve();
        window.speechSynthesis.speak(utterance);
      } else {
        console.error('Speech Synthesis not supported in this browser.');
        resolve();
      }
    });
  };

  // ---------- Typing effect + final persist ----------
  const simulateTypingEffect = (response: ChatbotResponse) => {
    const date = response.createdAt ? new Date(response.createdAt) : new Date();
    const datetime = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
    const messageId = Date.now();

    setTypingMessageId(messageId);
    setCurrentTypingText('');

    let currentIndex = 0;
    const typingInterval = setInterval(() => {
      if (currentIndex < response.response.length) {
        const currentText = response.response.substring(0, currentIndex + 1);
        setCurrentTypingText(currentText);
        currentIndex += 1;
      } else {
        setCurrentTypingText('');
        setTypingMessageId(null);
        clearInterval(typingInterval);

        // store meta for this message id
        messageMetaRef.current.set(messageId, {
          entities: response.entities || [],
          model: response.model || '',
          timeTaken: response.timeTaken || 0,
        });

        const finalMessage: ChatMessage = {
          id: messageId,
          user: 'chatbot',
          message: response.response,
          datetime: datetime,
          isTyping: false,
          src: response.src || [],
        } as ChatMessage;
        addMessageToCurrentSession(finalMessage);
      }
    }, 20);
  };

  // ---------- Submit (backend integration) ----------
  const handleSubmit = async (e: { preventDefault: () => void }) => {
    e.preventDefault();
    if (!inputMessage.trim() || !currentSession) {
      return;
    }

    const date = new Date();
    const datetime = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
    const createdAtISO = toLocalISOString(date);
    const userMessage: ChatMessage = {
      id: Date.now(),
      user: 'user',
      message: inputMessage,
      datetime: datetime,
    } as ChatMessage;

    addMessageToCurrentSession(userMessage);
    setInputMessage('');
    setIsLoading(true);

    // placeholder typing bubble
    simulateTypingEffect({ response: ' ', src: [] });

    try {
      const call = await chatBotAPI(inputMessage, currentSession.id, createdAtISO);
      const chatresponse = call.response;
      const answer: string = chatresponse.answer ?? chatresponse.response ?? '';
      const created_at: string = chatresponse.created_at ?? new Date().toISOString();
      const sources: string[] = Array.isArray(chatresponse.retriever_result)
        ? chatresponse.retriever_result.flatMap((s: { listIds?: string[] }) => s.listIds || [])
        : [];
      const entities: string[] = Array.isArray(chatresponse.retriever_result)
        ? chatresponse.retriever_result.flatMap((s: { entities?: string[] }) => s.entities || [])
        : [];

      const reply: ChatbotResponse = {
        response: answer,
        src: sources,
        entities,
        model: chatresponse.model || 'OpenAI GPT o3-mini',
        timeTaken: call.timeTaken,
        createdAt: created_at,
      };
      // replace the placeholder typing with the real stream
      simulateTypingEffect(reply);
    } catch (err) {
      console.error('Error Posting the Question:', err);
      simulateTypingEffect({
        response: 'Lo siento, hubo un problema al conectar con el servidor. Intenta nuevamente en unos segundos.',
        src: [],
      });
    } finally {
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages, typingMessageId, currentTypingText, isLoading]);

  const handleNewSession = () => {
    createNewSession();
  };

  const handleSwitchSession = (sessionId: string) => {
    switchSession(sessionId);
  };

  const handleDeleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    deleteSession(sessionId);
  };

  const handleEditSession = (sessionId: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(sessionId);
    setEditTitle(currentTitle);
  };

  const handleSaveEdit = (sessionId: string) => {
    if (editTitle.trim()) {
      updateSessionTitle(sessionId, editTitle.trim());
    }
    setEditingSessionId(null);
    setEditTitle('');
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditTitle('');
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) {
      return 'Today';
    }
    if (diffDays === 2) {
      return 'Yesterday';
    }
    if (diffDays < 7) {
      return `${diffDays - 1} days ago`;
    }
    return date.toLocaleDateString();
  };

  const currentMessages = currentSession?.messages || [];

  useEffect(() => {
    if (currentSession?.title) {
      document.title = `${currentSession.title} - DrChat`;
    } else {
      document.title = 'DrChat';
    }

    return () => {
      document.title = 'DrChat';
    };
  }, [currentSession?.title]);

  return (
    <div className='h-screen flex relative overflow-hidden n-bg-palette-neutral-bg-default'>
      <Drawer isExpanded={isDrawerOpen} onExpandedChange={setIsDrawerOpen} type='push' isCloseable={false}>
        <Drawer.Header>
          <div className='flex items-center justify-between w-full gap-2'>
            <Button color='neutral' onClick={handleNewSession} fill='outlined'>
              <PencilSquareIconOutline className='w-4 h-4 mr-4' /> New chat
            </Button>
            <Button
              color='neutral'
              fill='outlined'
              onClick={() => fileInputRef.current?.click()}
              isDisabled={uploadingSessionId === currentSession?.id || !currentSession}
            >
              <ArrowUpTrayIconOutline className='w-4 h-4 mr-4' /> Upload file
            </Button>
            <input
              ref={fileInputRef}
              type='file'
              accept='application/pdf'
              className='hidden'
              onChange={handleFileInputChange}
            />
          </div>
        </Drawer.Header>
        <Drawer.Body>
          <div className='space-y-4'>
            <section>
              <button
                type='button'
                className='flex w-full items-center justify-between rounded-lg px-2 py-1 hover:n-bg-palette-neutral-bg-weak'
                onClick={() => setIsChatListOpen((prev) => !prev)}
              >
                <Typography variant='body-medium' className='n-text-palette-neutral-text font-medium'>
                  Chats
                </Typography>
                {isChatListOpen ? (
                  <ChevronUpIconOutline className='w-4 h-4' />
                ) : (
                  <ChevronDownIconOutline className='w-4 h-4' />
                )}
              </button>
              {isChatListOpen ? (
                sessions.length === 0 ? (
                  <div className='flex flex-col p-4 text-center'>
                    <Typography variant='body-medium' className='n-text-palette-neutral-text-weak'>
                      No chat sessions yet.
                    </Typography>
                    <Button onClick={handleNewSession} className='mt-3' size='small'>
                      Start New Chat
                    </Button>
                  </div>
                ) : (
                  <div className='space-y-1 mt-2'>
                    {sessions.map((session) => {
                      const filesForSession = uploadedFilesBySession[session.id] ?? [];
                      const sessionError = uploadErrorsBySession[session.id] ?? null;
                      const isSessionUploading = uploadingSessionId === session.id;
                      const isFilesExpanded = expandedFilesSessions[session.id] ?? false;

                      return (
                        <div
                          key={session.id}
                          className={`group relative p-3 rounded-xl cursor-pointer transition-all duration-200 ${
                            session.id === currentSession?.id
                              ? 'n-bg-palette-primary-bg-selected'
                              : 'hover:n-bg-palette-primary-hover-weak'
                          }`}
                          onClick={() => handleSwitchSession(session.id)}
                        >
                          {editingSessionId === session.id ? (
                            <div className='flex items-center gap-2' onClick={(e) => e.stopPropagation()}>
                              <TextInput
                                value={editTitle}
                                onChange={(e) => setEditTitle(e.target.value)}
                                htmlAttributes={{
                                  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => {
                                    if (e.key === 'Enter') {
                                      handleSaveEdit(session.id);
                                    } else if (e.key === 'Escape') {
                                      handleCancelEdit();
                                    }
                                  },
                                  autoFocus: true,
                                }}
                                className='flex-1'
                                size='small'
                              />
                              <IconButton isClean ariaLabel='Save' onClick={() => handleSaveEdit(session.id)} size='small'>
                                <CheckIconOutline className='w-3 h-3' />
                              </IconButton>
                              <IconButton isClean ariaLabel='Cancel' onClick={handleCancelEdit} size='small'>
                                <XMarkIconOutline className='w-3 h-3' />
                              </IconButton>
                            </div>
                          ) : (
                            <div className='flex items-start justify-between'>
                              <div className='flex flex-col min-w-0'>
                                <Typography
                                  variant='body-medium'
                                  className={`truncate ${
                                    session.id === currentSession?.id
                                      ? 'n-text-palette-primary-text'
                                      : 'n-text-palette-neutral-text'
                                  }`}
                                >
                                  {session.title}
                                </Typography>
                                <Typography variant='body-small' className='n-text-palette-neutral-text-weak mt-1'>
                                  {formatDate(session.updatedAt)} • {session.messages.length} messages
                                </Typography>
                              </div>

                              <div className='flex ml-4 items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity'>
                                <IconButton
                                  isClean
                                  ariaLabel='Edit'
                                  onClick={(e) => handleEditSession(session.id, session.title, e)}
                                  size='small'
                                >
                                  <PencilSquareIconOutline className='w-3 h-3' />
                                </IconButton>
                                <IconButton
                                  isClean
                                  ariaLabel='Delete'
                                  onClick={(e) => handleDeleteSession(session.id, e)}
                                  size='small'
                                  className='n-text-palette-danger-text hover:n-bg-palette-danger-bg-weak'
                                >
                                  <TrashIconOutline className='w-3 h-3' />
                                </IconButton>
                              </div>
                            </div>
                          )}

                          <div className='mt-3 rounded-lg border border-[rgb(var(--theme-palette-neutral-border-weak))] p-2' onClick={(e) => e.stopPropagation()}>
                            <button
                              type='button'
                              className='flex w-full items-center justify-between rounded-md px-2 py-1 hover:n-bg-palette-neutral-bg-weak'
                              onClick={() =>
                                setExpandedFilesSessions((prev) => ({
                                  ...prev,
                                  [session.id]: !isFilesExpanded,
                                }))
                              }
                            >
                              <Typography variant='body-small' className='n-text-palette-neutral-text font-medium'>
                                Archivos ({filesForSession.length})
                              </Typography>
                              {isFilesExpanded ? (
                                <ChevronUpIconOutline className='w-4 h-4' />
                              ) : (
                                <ChevronDownIconOutline className='w-4 h-4' />
                              )}
                            </button>

                            {sessionError ? (
                              <Typography variant='body-small' className='mt-1 n-text-palette-danger-text'>
                                {sessionError}
                              </Typography>
                            ) : null}

                            {isSessionUploading ? (
                              <div className='mt-1 flex items-center gap-2'>
                                <LoadingSpinner size='small' />
                                <Typography variant='body-small' className='n-text-palette-neutral-text-weak'>
                                  Subiendo archivo...
                                </Typography>
                              </div>
                            ) : null}

                            {isFilesExpanded ? (
                              filesForSession.length > 0 ? (
                                <ul className='mt-2 space-y-3'>
                                  {filesForSession.map((file) => (
                                    <li
                                      key={file.id}
                                      className='rounded-lg border border-[rgb(var(--theme-palette-neutral-border-weak))] p-3 bg-[rgb(var(--theme-palette-neutral-bg-default))]'
                                    >
                                      <div className='flex items-start justify-between gap-2'>
                                        <div className='flex-1'>
                                          <Typography variant='body-medium' className='n-text-palette-neutral-text'>
                                            {file.name}
                                          </Typography>
                                          <div className='mt-1 grid grid-cols-[auto,1fr] gap-x-2 gap-y-1 text-left'>
                                            <Typography variant='body-small' className='n-text-palette-neutral-text-weak'>
                                              Estado:
                                            </Typography>
                                            <Typography variant='body-small' className='n-text-palette-neutral-text'>
                                              {file.status}
                                            </Typography>

                                            <Typography variant='body-small' className='n-text-palette-neutral-text-weak'>
                                              Subido:
                                            </Typography>
                                            <Typography variant='body-small' className='n-text-palette-neutral-text'>
                                              {new Date(file.uploadedAt).toLocaleString()}
                                            </Typography>

                                            <Typography variant='body-small' className='n-text-palette-neutral-text-weak'>
                                              Tamaño:
                                            </Typography>
                                            <Typography variant='body-small' className='n-text-palette-neutral-text'>
                                              {(file.size / 1024).toFixed(1)} KB
                                            </Typography>
                                          </div>
                                        </div>
                                      </div>
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                !isSessionUploading && !sessionError ? (
                                  <Typography variant='body-small' className='mt-2 n-text-palette-neutral-text-weak'>
                                    Aún no subiste archivos para este chat.
                                  </Typography>
                                ) : null
                              )
                            ) : null}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )
              ) : null}
            </section>

          </div>
        </Drawer.Body>
      </Drawer>

      <div className='flex-1 flex flex-col h-screen'>
        <div className='n-bg-palette-neutral-bg-weak p-4 flex items-center gap-4'>
          <IconButton
            isClean
            ariaLabel='Open Chat History'
            onClick={() => setIsDrawerOpen(!isDrawerOpen)}
            className='group relative hover:n-bg-palette-neutral-bg transition-all duration-200'
          >
            <SidebarLineLeftIcon className='w-6 h-6 opacity-100 group-hover:opacity-0 transition-opacity duration-200' />
            <ArrowRightIconOutline
              className={`absolute inset-0 w-6 h-6 m-auto opacity-0 group-hover:opacity-100 transition-opacity duration-200 ${
                isDrawerOpen ? 'hidden' : 'block'
              }`}
            />
            <ArrowLeftIconOutline
              className={`absolute inset-0 w-6 h-6 m-auto opacity-0 group-hover:opacity-100 transition-opacity duration-200 ${
                isDrawerOpen ? 'block' : 'hidden'
              }`}
            />
          </IconButton>
          <div>
            <Typography variant='h6' className='n-text-palette-neutral-text'>
              {currentSession?.title || 'New Chat'}
            </Typography>
            <Typography variant='body-small' className='n-text-palette-neutral-text-weak'>
              {(currentSession?.messages?.length || 0)} messages
            </Typography>
          </div>
        </div>

        <div className='flex-1 overflow-y-auto pb-6 n-bg-palette-neutral-bg-default'>
          <div className='flex flex-col gap-3 p-3 min-h-full'>
            {currentMessages.map((chat) => (
              <div
                ref={messagesEndRef}
                key={chat.id}
                className={`flex gap-2.5 items-end ${chat.user === 'chatbot' ? 'flex-row' : 'flex-row-reverse'} `}
              >
                <div className='w-8 h-8 mr-4 ml-4'>
                  {chat.user === 'chatbot' ? (
                    <Avatar
                      className='-ml-4'
                      hasStatus
                      name='KM'
                      size='x-large'
                      source={ChatBotAvatar}
                      status='online'
                      type='image'
                      shape='square'
                    />
                  ) : (
                    <Avatar
                      className=''
                      hasStatus
                      name='KM'
                      size='x-large'
                      status='online'
                      type='image'
                      shape='square'
                    />
                  )}
                </div>
                <Widget
                  header=''
                  isElevated={true}
                  className={`p-4 self-start max-w-[55%] ${
                    chat.user === 'chatbot' ? 'n-bg-palette-neutral-bg-weak' : 'n-bg-palette-primary-bg-weak'
                  }`}
                >
                  <div>
                    <ReactMarkdown
                      components={{
                        code: ({ children }) => <span style={formattedTextStyle}>{children}</span>,
                        a: ({ ...props }) => (
                          <TextLink type='external' href={props.href} target='_blank'>
                            {props.children}
                          </TextLink>
                        ),
                      }}
                      remarkPlugins={[remarkGfm]}
                    >
                      {chat.message}
                    </ReactMarkdown>
                  </div>
                  <div className='text-right align-bottom pt-3'>
                    <Typography variant='body-small'>{chat.datetime}</Typography>
                  </div>
                  <Typography variant='body-small' className='text-right'>
                    {chat.user === 'chatbot' ? (
                      <div className='flex gap-1'>
                        {/* Audio / Voice */}
                        <IconButton
                          isClean
                          ariaLabel='Read out'
                          isDisabled={isLoading || chat.isTyping}
                          onClick={async () => {
                            setLoadingPlaying(true);
                            await chatBotVoice(chat.message);
                            setLoadingPlaying(false);
                          }}
                        >
                          {loadingPlaying ? (
                            <LoadingSpinner className='w-4 h-4 inline-block' />
                          ) : (
                            <SpeakerWaveIconOutline className='w-4 h-4 inline-block' />
                          )}
                        </IconButton>

                        {/* Graphs / Sources modal */}
                        {(chat.src && chat.src.length > 0) && (
                          <IconButton
                            isClean
                            ariaLabel='Show graphs & sources'
                            onClick={() => {
                              const meta = messageMetaRef.current.get(chat.id);
                              setModelModal(meta?.model || '');
                              setEntitiesModal(meta?.entities || []);
                              setTimeTaken(meta?.timeTaken || 0);
                              setSourcesModal(chat.src ?? []);
                              setIsOpenModal(true);
                            }}
                          >
                            <PiGraphBold className='w-4 h-4 inline-block' />
                          </IconButton>
                        )}

                        {/* Info (kept from original) */}
                        {chat.src && chat.src.length > 0 ? (
                          <IconButton
                            isClean
                            ariaLabel='Info'
                            onClick={() => {
                              const meta = messageMetaRef.current.get(chat.id);
                              setModelModal(meta?.model || '');
                              setSourcesModal(chat.src ?? []);
                              setTimeTaken(meta?.timeTaken || 0);
                              setEntitiesModal(meta?.entities || []);
                              setIsOpenModal(true);
                            }}
                          >
                            <InformationCircleIconOutline className='w-4 h-4 inline-block' />
                          </IconButton>
                        ) : null}

                        {/* Copy */}
                        <IconButton isClean ariaLabel='Copy' onClick={() => copy(chat.message)}>
                          <ClipboardDocumentIconOutline className='w-4 h-4 inline-block' />
                        </IconButton>

                        {/* Regenerate (kept as visual only) */}
                        <IconButton isClean ariaLabel='Regenerate'>
                          <ArrowPathIconOutline className='w-4 h-4 inline-block' />
                        </IconButton>

                        {/* Like / Dislike */}
                        <IconButton
                          isClean
                          ariaLabel='Like'
                          onClick={() => sendFeedback(chat.id, true)}
                          isDisabled={isLoading || chat.isTyping}
                        >
                          <HandThumbUpIconOutline className='w-4 h-4 inline-block n-text-palette-success-text' />
                        </IconButton>
                        <IconButton
                          isClean
                          ariaLabel='Dislike'
                          onClick={() => sendFeedback(chat.id, false)}
                          isDisabled={isLoading || chat.isTyping}
                        >
                          <HandThumbDownIconOutline className='w-4 h-4 inline-block n-text-palette-danger-text' />
                        </IconButton>
                      </div>
                    ) : (
                      <></>
                    )}
                  </Typography>
                </Widget>
              </div>
            ))}

            {isLoading && (
              <div ref={messagesEndRef} className='flex gap-2.5 items-end flex-row'>
                <div className='w-8 h-8 mr-4 ml-4'>
                  <Avatar
                    className='-ml-4'
                    hasStatus
                    name='KM'
                    size='x-large'
                    source={ChatBotAvatar}
                    status='online'
                    type='image'
                    shape='square'
                  />
                </div>
                <Widget header='' isElevated={true} className='p-4 self-start max-w-[55%] n-bg-palette-neutral-bg-weak'>
                  <div className='flex items-center gap-2'>
                    <LoadingSpinner size='small' />
                    <Typography variant='body-medium'>Thinking...</Typography>
                  </div>
                </Widget>
              </div>
            )}

            {typingMessageId && currentTypingText && (
              <div ref={messagesEndRef} className='flex gap-2.5 items-end flex-row'>
                <div className='w-8 h-8 mr-4 ml-4'>
                  <Avatar
                    className='-ml-4'
                    hasStatus
                    name='KM'
                    size='x-large'
                    source={ChatBotAvatar}
                    status='online'
                    type='image'
                    shape='square'
                  />
                </div>
                <Widget header='' isElevated={true} className='p-4 self-start max-w-[55%] n-bg-palette-neutral-bg-weak'>
                  <div>
                    <ReactMarkdown
                      components={{
                        code: ({ children }) => <span style={formattedTextStyle}>{children}</span>,
                        a: ({ ...props }) => (
                          <TextLink type='external' href={props.href} target='_blank'>
                            {props.children}
                          </TextLink>
                        ),
                      }}
                      remarkPlugins={[remarkGfm]}
                    >
                      {currentTypingText}
                    </ReactMarkdown>
                  </div>
                  <div className='text-right align-bottom pt-3'>
                    <Typography variant='body-small'>Typing...</Typography>
                  </div>
                </Widget>
              </div>
            )}
          </div>
        </div>

        <div className='n-bg-palette-neutral-bg-default border-t n-border-palette-neutral-border-weak p-4'>
          <form onSubmit={handleSubmit} className='flex gap-2.5 w-full'>
            <TextInput
              className='flex-1'
              value={inputMessage}
              isFluid
              onChange={handleInputChange}
              htmlAttributes={{
                type: 'text',
                'aria-label': 'Chatbot Input',
                placeholder: 'Type your message...',
              }}
            />
            <Button type='submit' isDisabled={!inputMessage.trim()}>
              Send
            </Button>
          </form>
        </div>

        <Modal
          modalProps={{
            id: 'default-menu',
            className: 'n-p-token-4 n-bg-palette-neutral-bg-weak n-rounded-lg min-w-[60%] max-h-[80%]',
          }}
          onClose={handleCloseModal}
          isOpen={isOpenModal}
        >
          <RetrievalInformation
            sources={sourcesModal}
            model={modelModal}
            timeTaken={timeTaken}
            entities={entitiesModal}
          />
        </Modal>
      </div>
    </div>
  );
}
