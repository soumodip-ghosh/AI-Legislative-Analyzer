import { useState } from "react";
import { motion } from "framer-motion";
import { MessageCircle, Send, Bot, User } from "lucide-react";
import axios from "axios";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatCardProps {
  docHash: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function ChatCard({ docHash }: ChatCardProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const { data } = await axios.post(`${API_BASE}/chat`, {
        question: input,
        doc_hash: docHash,
      });

      const assistantMessage: Message = { role: "assistant", content: data.answer };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        role: "assistant",
        content: error.response?.data?.detail || "Sorry, I couldn't answer that question. Please try again.",
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="glass rounded-2xl p-6 border border-white/6">
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-8 h-8 rounded-xl bg-blue-400/10 flex items-center justify-center">
          <MessageCircle className="w-4 h-4 text-blue-400" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">Ask Questions</h3>
          <p className="text-xs text-slate-500">Get answers about this document</p>
        </div>
      </div>

      {/* Messages */}
      <div className="space-y-4 mb-4 max-h-64 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="text-center text-slate-500 text-sm py-8">
            Ask me anything about the document!
          </div>
        ) : (
          messages.map((msg, i) => (
            <motion.div
              key={i}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              {msg.role === "assistant" && (
                <div className="w-6 h-6 rounded-full bg-blue-400/10 flex items-center justify-center flex-shrink-0 mt-1">
                  <Bot className="w-3 h-3 text-blue-400" />
                </div>
              )}
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl text-sm ${
                  msg.role === "user"
                    ? "bg-blue-400 text-white ml-auto"
                    : "bg-white/5 text-slate-300"
                }`}
              >
                {msg.content}
              </div>
              {msg.role === "user" && (
                <div className="w-6 h-6 rounded-full bg-slate-600 flex items-center justify-center flex-shrink-0 mt-1">
                  <User className="w-3 h-3 text-white" />
                </div>
              )}
            </motion.div>
          ))
        )}
        {loading && (
          <motion.div className="flex gap-3 justify-start" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="w-6 h-6 rounded-full bg-blue-400/10 flex items-center justify-center flex-shrink-0 mt-1">
              <Bot className="w-3 h-3 text-blue-400" />
            </div>
            <div className="bg-white/5 px-4 py-2 rounded-2xl text-sm text-slate-300">
              Thinking...
            </div>
          </motion.div>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question about the document..."
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-400/50"
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || loading}
          className="bg-blue-400 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white p-2 rounded-xl transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}