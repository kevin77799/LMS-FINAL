import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Chat as ChatApi } from "@/api/endpoints";
import { MessageSquarePlus, Clock, Send, Loader2, User, Bot } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  message: string;
  timestamp?: string;
}

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}

export default function Chat() {
  const nav = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  const [groupId, setGroupId] = useState<number | null>(
    Number(localStorage.getItem("group_id")) || null
  );
  const [activeSessionId, setActiveSessionId] = useState<string>(
    localStorage.getItem("active_chat_session") || Date.now().toString()
  );
  const [sessions, setSessions] = useState<ChatSession[]>([]);

  const [mode, setMode] = useState<"text" | "image" | "video">("text");
  const [prompt, setPrompt] = useState("");
  const [history, setHistory] = useState<Message[]>([]);
  const [file, setFile] = useState<File>();
  const [imageUrl, setImageUrl] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);

  // Persistence
  useEffect(() => {
    if (groupId) localStorage.setItem("group_id", String(groupId));
    localStorage.setItem("active_chat_session", activeSessionId);
  }, [groupId, activeSessionId]);

  const loadSessions = async () => {
    if (!groupId || !user.user_id) return;
    try {
      const s = await ChatApi.listSessions(user.user_id, groupId);
      setSessions(s);
    } catch (e) {
      console.error("Failed to load sessions:", e);
    }
  };

  const loadHistory = async (sid?: string) => {
    const targetSid = sid || activeSessionId;
    if (!groupId || !user.user_id || mode !== "text") return;

    setIsHistoryLoading(true);
    try {
      const h = await ChatApi.textHistory(groupId, user.user_id, targetSid);
      setHistory(h);
    } catch (error) {
      console.error("Failed to load history:", error);
      setHistory([]);
    } finally {
      setIsHistoryLoading(false);
    }
  };

  useEffect(() => {
    if (!user?.username) nav("/login");
  }, [user, nav]);

  useEffect(() => {
    loadSessions();
    loadHistory();
  }, [groupId, mode, activeSessionId]);

  const createNewChat = () => {
    const newId = Date.now().toString();
    setActiveSessionId(newId);
    setHistory([]);
    setPrompt("");
    setMode("text");
  };

  const sendMessage = async () => {
    if (!groupId || !prompt) return;
    setIsLoading(true);

    const userMessage: Message = { role: "user", message: prompt };
    setHistory(prev => [...prev, userMessage]);
    const currentPrompt = prompt;
    setPrompt("");

    try {
      let aiResponse: { response: string } | undefined;

      if (mode === "text") {
        await ChatApi.text(groupId, user.user_id, currentPrompt, activeSessionId);
        await loadHistory();
        await loadSessions(); // Refresh title if it's the first message
        return;
      } else if (mode === "image") {
        aiResponse = await ChatApi.image(groupId, user.user_id, currentPrompt, activeSessionId, file, imageUrl || undefined);
      } else {
        aiResponse = await ChatApi.video(groupId, user.user_id, currentPrompt, activeSessionId, videoUrl);
      }

      if (aiResponse) {
        setHistory(prev => [...prev, { role: "assistant", message: aiResponse!.response }]);
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      setHistory(prev => [...prev, { role: "assistant", message: "Sorry, something went wrong." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex flex-col md:flex-row h-[calc(100vh-140px)] gap-6 animate-in fade-in duration-500">

      {/* Sidebar: Chat History */}
      <div className="w-full md:w-80 flex flex-col bg-theme-surface border border-theme-border rounded-xl p-4 overflow-hidden shadow-lg">
        <button
          onClick={createNewChat}
          className="flex items-center justify-center gap-2 w-full py-3 bg-theme-accent text-theme-bg font-bold rounded-lg hover:bg-theme-accent-hover transition-all mb-6 shadow-md"
        >
          <MessageSquarePlus size={18} />
          New Chat Session
        </button>

        <div className="flex-1 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
          <h3 className="text-xs font-black uppercase text-theme-text-secondary tracking-widest mb-3 flex items-center gap-2">
            <Clock size={12} /> Previous Chats
          </h3>

          {sessions.length === 0 && !isHistoryLoading && (
            <p className="text-sm text-theme-text-secondary italic p-4 text-center">No previous chats yet.</p>
          )}

          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSessionId(s.id)}
              className={`w-full p-4 rounded-xl text-left border transition-all duration-200 group ${activeSessionId === s.id
                ? 'bg-theme-accent/10 border-theme-accent shadow-inner'
                : 'bg-theme-bg/50 border-theme-border hover:border-theme-text-secondary hover:bg-white/5'
                }`}
            >
              <p className={`font-bold text-sm truncate ${activeSessionId === s.id ? 'text-theme-accent' : 'text-theme-text'}`}>
                {s.title}
              </p>
              <p className="text-[10px] text-theme-text-secondary mt-1 font-mono uppercase">
                {formatDate(s.created_at)}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-theme-surface border border-theme-border rounded-xl shadow-lg relative overflow-hidden">

        {/* Chat Header */}
        <div className="p-4 border-b border-theme-border bg-theme-accent/5 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-theme-accent/20 flex items-center justify-center text-theme-accent border border-theme-accent/30">
              <Bot size={20} />
            </div>
            <div>
              <h2 className="font-black text-theme-text">AI Study Assistant</h2>
              <p className="text-[10px] text-theme-text-secondary uppercase font-bold">Mode: {mode}</p>
            </div>
          </div>

          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Group"
              value={groupId ?? ""}
              onChange={(e) => setGroupId(Number(e.target.value))}
              className="w-20 px-3 py-1.5 rounded-md bg-theme-bg border border-theme-border outline-none text-xs font-mono"
            />
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as any)}
              className="px-3 py-1.5 rounded-md bg-theme-bg border border-theme-border outline-none text-xs font-bold"
            >
              <option value="text">TEXT</option>
              <option value="image">IMAGE</option>
              <option value="video">VIDEO</option>
            </select>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar bg-theme-bg/20">
          {history.length === 0 && !isHistoryLoading && (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-40">
              <Bot size={48} className="mb-4 text-theme-accent" />
              <h3 className="text-lg font-bold">Ready to Learn?</h3>
              <p className="max-w-[250px] text-sm">Ask me any question about your syllabus or uploaded reports.</p>
            </div>
          )}

          {isHistoryLoading && (
            <div className="flex justify-center p-10">
              <Loader2 className="animate-spin text-theme-accent" size={32} />
            </div>
          )}

          {history.map((h, i) => (
            <div key={i} className={`flex items-start gap-3 ${h.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`p-2 rounded-full border ${h.role === 'user' ? 'bg-theme-accent text-theme-bg border-theme-accent' : 'bg-theme-surface text-theme-accent border-theme-border'}`}>
                {h.role === 'user' ? <User size={14} /> : <Bot size={14} />}
              </div>
              <div className={`p-4 rounded-2xl max-w-[85%] shadow-sm ${h.role === "user"
                ? "bg-theme-accent/20 text-theme-text font-medium border border-theme-accent/20"
                : "bg-theme-surface border border-theme-border text-theme-text-secondary leading-relaxed"
                }`}>
                <p className="text-sm">{h.message}</p>
                {h.timestamp && <p className="text-[9px] mt-2 opacity-50 font-mono">{new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-full border bg-theme-surface text-theme-accent border-theme-border animate-pulse">
                <Bot size={14} />
              </div>
              <div className="p-4 rounded-2xl bg-theme-surface border border-theme-border flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-theme-accent rounded-full animate-bounce"></span>
                <span className="w-1.5 h-1.5 bg-theme-accent rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-1.5 h-1.5 bg-theme-accent rounded-full animate-bounce [animation-delay:-0.3s]"></span>
              </div>
            </div>
          )}
        </div>

        {/* Input Footer */}
        <div className="p-4 border-t border-theme-border bg-theme-surface">

          {mode === "image" && (
            <div className="mb-3 p-3 bg-theme-bg/50 rounded-lg border border-dashed border-theme-border flex flex-col md:flex-row gap-3">
              <input type="file" onChange={(e) => setFile(e.target.files?.[0])} className="text-xs text-theme-text-secondary" />
              <input className="flex-1 px-3 py-1.5 rounded bg-theme-bg border border-theme-border outline-none text-xs" placeholder="or Image URL..." value={imageUrl} onChange={(e) => setImageUrl(e.target.value)} />
            </div>
          )}

          {mode === "video" && (
            <div className="mb-3">
              <input className="w-full px-3 py-2 rounded-lg bg-theme-bg border border-theme-border outline-none text-sm font-mono" placeholder="Paste YouTube Video URL..." value={videoUrl} onChange={(e) => setVideoUrl(e.target.value)} />
            </div>
          )}

          <div className="flex gap-2 relative">
            <input
              className="flex-1 h-12 px-5 rounded-full bg-theme-bg border border-theme-border focus:border-theme-accent outline-none text-theme-text pr-14 transition-all"
              placeholder="Ask anything..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !isLoading && sendMessage()}
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !prompt.trim()}
              className="absolute right-1 top-1 w-10 h-10 flex items-center justify-center rounded-full bg-theme-accent text-theme-bg hover:bg-theme-accent-hover transition-colors disabled:opacity-30 disabled:grayscale shadow-md"
            >
              {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </div>
          <p className="text-[10px] text-center text-theme-text-secondary mt-3 uppercase tracking-tighter">Powered by Gemini 2.0 Flash AI</p>
        </div>
      </div>
    </div>
  );
}
