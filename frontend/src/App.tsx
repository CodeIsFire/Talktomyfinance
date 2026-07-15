import { FormEvent, useEffect, useRef, useState } from 'react';
import { usePlaidLink } from 'react-plaid-link';

type Message = {
  id: number;
  role: 'user' | 'assistant' | 'error';
  content: string;
  latencyMs?: number;
  grounded?: boolean;
};

type VoiceState = 'idle' | 'listening' | 'thinking' | 'speaking';

type SpeechRecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  onstart: (() => void) | null;
  onresult: ((event: any) => void) | null;
  onerror: ((event: any) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  }
}

const initialMessages: Message[] = [
  {
    id: 1,
    role: 'assistant',
    content: 'Hi! Ask me about your spending, subscriptions, or merchant trends.',
  },
];

function App() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [voiceSupported, setVoiceSupported] = useState(true);
  const [mute, setMute] = useState(false);
  const [voiceNote, setVoiceNote] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const silenceTimerRef = useRef<number | null>(null);
  const voiceStateRef = useRef<VoiceState>('idle');
  const permissionRequestedRef = useRef(false);

  useEffect(() => {
    voiceStateRef.current = voiceState;
  }, [voiceState]);

  const createRecognition = () => {
    const SpeechCtor = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!SpeechCtor) {
      setVoiceSupported(false);
      setVoiceNote('Speech recognition is not supported in this browser. You can still type and send messages normally.');
      return null;
    }

    const recognition = new SpeechCtor();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setVoiceState('listening');
      setVoiceNote('Listening...');
    };

    recognition.onresult = (event: any) => {
      const interimText = Array.from(event.results)
        .map((result: any) => result[0]?.transcript ?? '')
        .join(' ')
        .trim();

      if (event.results[event.resultIndex]?.isFinal) {
        const finalText = interimText;
        setVoiceTranscript(finalText);
        setInput(finalText);
        setVoiceState('idle');
        if (silenceTimerRef.current) {
          window.clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
        recognition.stop();
      } else {
        setVoiceTranscript(interimText);
      }
    };

    recognition.onerror = (event: any) => {
      const message = event.error === 'not-allowed'
        ? 'Microphone access was blocked. Please allow microphone access and try again.'
        : event.error === 'no-speech'
          ? 'No speech was detected. Please try again.'
          : 'Voice input could not be started. Please try again.';
      setVoiceNote(message);
      setVoiceState('idle');
    };

    recognition.onend = () => {
      if (silenceTimerRef.current) {
        window.clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
      if (voiceStateRef.current === 'listening') {
        setVoiceState('idle');
      }
    };

    return recognition;
  };

  useEffect(() => {
    const loadLinkToken = async () => {
      try {
        const response = await fetch('/api/plaid/create_link_token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: 'demo-user' }),
        });
        const data = await response.json();
        if (data.link_token) {
          setLinkToken(data.link_token);
        }
      } catch {
        // Ignore missing credentials during demo.
      }
    };
    void loadLinkToken();
  }, []);

  useEffect(() => {
    const recognition = createRecognition();
    recognitionRef.current = recognition;

    return () => {
      recognition?.stop();
      if (silenceTimerRef.current) {
        window.clearTimeout(silenceTimerRef.current);
      }
    };
  }, []);

  const { open } = usePlaidLink({
    token: linkToken ?? '',
    onSuccess: async (publicToken) => {
      try {
        const response = await fetch('/api/plaid/exchange_token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ public_token: publicToken }),
        });
        if (response.ok) {
          setConnected(true);
          setMessages((current) => [
            ...current,
            {
              id: Date.now(),
              role: 'assistant',
              content: 'Bank account connected. Your Plaid transactions will be used for future analysis.',
            },
          ]);
        }
      } catch {
        // Ignore errors in demo mode.
      }
    },
    onExit: () => undefined,
  });

  const formatForTts = (text: string) => {
    const formatted = text
      .replace(/₹/g, 'rupees ')
      .replace(/\$/g, 'dollars ')
      .replace(/€/g, 'euros ')
      .replace(/£/g, 'pounds ')
      .replace(/%/g, ' percent ')
      .replace(/(\d+)\.(\d+)/g, '$1 point $2')
      .replace(/\n+/g, '. ')
      .replace(/([.!?])\s+/g, '$1 ')
      .trim();

    return formatted.length > 0 ? `${formatted} .` : formatted;
  };

  const speakText = (text: string) => {
    if (mute || typeof window === 'undefined' || !('speechSynthesis' in window)) {
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(formatForTts(text));
    utterance.lang = 'en-US';
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.onstart = () => setVoiceState('speaking');
    utterance.onend = () => setVoiceState('idle');
    utterance.onerror = () => setVoiceState('idle');
    window.speechSynthesis.speak(utterance);
  };

  const handleVoiceToggle = async () => {
    if (!voiceSupported) {
      return;
    }

    if (voiceStateRef.current === 'listening') {
      recognitionRef.current?.stop();
      setVoiceState('idle');
      setVoiceTranscript('');
      return;
    }

    if (voiceStateRef.current === 'thinking') {
      return;
    }

    if (voiceStateRef.current === 'speaking') {
      window.speechSynthesis.cancel();
    }

    setVoiceNote(null);
    setVoiceTranscript('');

    if (typeof navigator !== 'undefined' && navigator.mediaDevices?.getUserMedia) {
      try {
        if (!permissionRequestedRef.current) {
          permissionRequestedRef.current = true;
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          stream.getTracks().forEach((track) => track.stop());
        }
      } catch (error) {
        const isBlocked = error instanceof DOMException && error.name === 'NotAllowedError';
        setVoiceState('idle');
        setVoiceNote(isBlocked ? 'Microphone access was blocked. Please allow mic access and try again.' : 'Voice input could not be started.');
        return;
      }
    } else {
      setVoiceState('idle');
      setVoiceNote('This browser does not expose microphone access. Please use a compatible browser.');
      return;
    }

    const freshRecognition = createRecognition();
    if (!freshRecognition) {
      setVoiceState('idle');
      return;
    }

    recognitionRef.current = freshRecognition;

    if (silenceTimerRef.current) {
      window.clearTimeout(silenceTimerRef.current);
    }

    try {
      freshRecognition.start();
      silenceTimerRef.current = window.setTimeout(() => {
        freshRecognition.stop();
      }, 4000);
    } catch {
      setVoiceState('idle');
      setVoiceNote('Voice input could not be started. Please try again.');
    }
  };

  const handleReplay = (content: string) => {
    if (mute) {
      return;
    }
    setVoiceState('speaking');
    speakText(content);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;

    const userMessage: Message = { id: Date.now(), role: 'user', content: trimmed };
    setMessages((current) => [...current, userMessage]);
    setInput('');
    setLoading(true);
    setVoiceState('thinking');
    setVoiceTranscript('');

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmed }),
      });

      if (!response.ok) {
        throw new Error('Request failed');
      }

      const data = await response.json();
      const assistantMessage: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.answer,
        latencyMs: data.latency_ms,
        grounded: data.grounded,
      };
      setMessages((current) => [...current, assistantMessage]);
      if (!mute) {
        speakText(assistantMessage.content);
      }
    } catch {
      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 2,
          role: 'error',
          content: 'Unable to reach the assistant right now. Please make sure the backend is running.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 p-4 text-slate-100 sm:p-6 lg:p-8">
      <div className="mx-auto flex max-w-4xl flex-col rounded-3xl border border-slate-800 bg-slate-900/80 shadow-2xl shadow-black/40 backdrop-blur">
        <header className="border-b border-slate-800 px-6 py-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-cyan-400">AI Finance Voice Assistant</p>
              <h1 className="text-xl font-semibold">Ask about your money in plain English</h1>
            </div>
            <div className="flex items-center gap-2">
              <span className={`rounded-full px-3 py-1 text-sm ${connected ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-300'}`}>
                {connected ? 'Connected' : 'Not connected'}
              </span>
              <button
                type="button"
                onClick={() => setMute((current) => !current)}
                className="rounded-full border border-slate-700 px-3 py-2 text-sm text-slate-300 transition hover:border-cyan-500 hover:text-cyan-300"
              >
                {mute ? '🔈 Mute' : '🔊 Speak'}
              </button>
              <button
                type="button"
                onClick={() => {
                  if (linkToken) {
                    open?.();
                  }
                }}
                className="rounded-full border border-slate-700 px-3 py-2 text-sm text-slate-300 transition hover:border-cyan-500 hover:text-cyan-300"
              >
                Connect Bank Account
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 space-y-4 overflow-y-auto px-4 py-5 sm:px-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-lg sm:max-w-[75%] ${
                  message.role === 'user'
                    ? 'bg-cyan-600 text-white'
                    : message.role === 'error'
                      ? 'border border-rose-500/40 bg-rose-950/70 text-rose-100'
                      : 'border border-slate-800 bg-slate-800/90 text-slate-100'
                }`}
              >
                <p className="whitespace-pre-wrap leading-7">{message.content}</p>
                {message.role === 'assistant' && (
                  <div className="mt-3 flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {message.grounded !== undefined && (
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                            message.grounded
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : 'bg-amber-500/20 text-amber-300'
                          }`}
                        >
                          {message.grounded ? 'Grounded' : 'Ungrounded'}
                        </span>
                      )}
                      {message.latencyMs !== undefined && (
                        <span className="text-[11px] text-slate-400">{message.latencyMs}ms</span>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => handleReplay(message.content)}
                      className="rounded-full border border-slate-700 p-2 text-slate-300 transition hover:border-cyan-500 hover:text-cyan-300"
                      title="Replay response"
                    >
                      🔊
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-slate-800 bg-slate-800/90 px-4 py-3">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-400" />
                  <span>Thinking</span>
                </div>
              </div>
            </div>
          )}
        </main>

        <form onSubmit={handleSubmit} className="border-t border-slate-800 p-4 sm:p-6">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className={`h-2.5 w-2.5 rounded-full ${voiceState === 'listening' ? 'animate-pulse bg-rose-500' : voiceState === 'thinking' ? 'animate-pulse bg-amber-400' : voiceState === 'speaking' ? 'animate-pulse bg-emerald-500' : 'bg-slate-500'}`} />
              <span>{voiceState === 'listening' ? 'Listening' : voiceState === 'thinking' ? 'Thinking' : voiceState === 'speaking' ? 'Speaking' : 'Idle'}</span>
              {voiceTranscript && <span className="text-slate-400">• {voiceTranscript}</span>}
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask: how much did I spend on subscriptions last month?"
                className="flex-1 rounded-2xl border border-slate-700 bg-slate-950/80 px-4 py-3 text-sm outline-none ring-0 transition focus:border-cyan-500"
              />
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="rounded-2xl bg-cyan-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-cyan-500"
                >
                  Send
                </button>
                <button
                  type="button"
                  onClick={() => void handleVoiceToggle()}
                  disabled={loading || !voiceSupported}
                  className={`rounded-2xl border px-3 py-3 text-sm transition ${
                    voiceState === 'listening'
                      ? 'border-rose-500 bg-rose-500/20 text-rose-300'
                      : 'border-slate-700 text-slate-300 hover:border-cyan-500 hover:text-cyan-300'
                  } ${loading || !voiceSupported ? 'cursor-not-allowed opacity-60' : ''}`}
                  title={voiceSupported ? 'Toggle voice input' : 'Voice input not supported'}
                >
                  {voiceState === 'listening' ? '🔴' : '🎤'}
                </button>
              </div>
            </div>
            {voiceNote && <p className="text-xs text-amber-300">{voiceNote}</p>}
          </div>
        </form>
      </div>
    </div>
  );
}

export default App;
