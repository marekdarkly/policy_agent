import { useState, useRef, useEffect } from "react";
import { Send, X, Bot, User, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
}

interface ChatWidgetProps {
  isOpen: boolean;
  onClose: () => void;
  initialQuery?: string;
}

const DOMAIN = "togglecell";

const ChatWidget = ({ isOpen, onClose, initialQuery }: ChatWidgetProps) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "0",
      role: "assistant",
      content:
        "Hi there! I'm your ToggleCell support assistant. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const hasProcessedInitial = useRef(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && initialQuery && !hasProcessedInitial.current) {
      hasProcessedInitial.current = true;
      sendMessage(initialQuery);
    }
  }, [isOpen, initialQuery]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text.trim(),
    };
    const loadingMsg: Message = {
      id: (Date.now() + 1).toString(),
      role: "system",
      content: "loading",
    };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userInput: text.trim(),
          domain: DOMAIN,
          userName: "Demo User",
          location: "London, UK",
          policyId: "TC-5G-UNLIM-2026",
          coverageType: "5G Unlimited",
        }),
      });

      const data = await response.json();

      setMessages((prev) =>
        prev
          .filter((m) => m.content !== "loading")
          .concat({
            id: (Date.now() + 2).toString(),
            role: "assistant",
            content:
              data.response || "Sorry, I couldn't process that request.",
          })
      );
    } catch {
      setMessages((prev) =>
        prev
          .filter((m) => m.content !== "loading")
          .concat({
            id: (Date.now() + 2).toString(),
            role: "assistant",
            content: "Sorry, something went wrong. Please try again.",
          })
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.95 }}
          transition={{ duration: 0.2 }}
          className="fixed bottom-6 right-6 w-[420px] h-[600px] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden z-50 border border-gray-200"
        >
          {/* Header */}
          <div className="bg-[hsl(0,100%,45%)] px-5 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-white/20 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-sm">
                  ToggleCell Support
                </h3>
                <p className="text-white/70 text-xs">
                  Powered by Amazon Bedrock
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white/70 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {messages.map((msg) => {
              if (msg.content === "loading") {
                return (
                  <div key={msg.id} className="flex items-start gap-2">
                    <div className="w-7 h-7 bg-[hsl(0,100%,45%)]/10 rounded-full flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-[hsl(0,100%,45%)]" />
                    </div>
                    <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
                      <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                    </div>
                  </div>
                );
              }

              if (msg.role === "user") {
                return (
                  <div key={msg.id} className="flex items-start gap-2 justify-end">
                    <div className="bg-[hsl(0,100%,45%)] text-white rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-[80%]">
                      <p className="text-sm">{msg.content}</p>
                    </div>
                    <div className="w-7 h-7 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-gray-500" />
                    </div>
                  </div>
                );
              }

              return (
                <div key={msg.id} className="flex items-start gap-2">
                  <div className="w-7 h-7 bg-[hsl(0,100%,45%)]/10 rounded-full flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-[hsl(0,100%,45%)]" />
                  </div>
                  <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-2.5 max-w-[80%] prose prose-sm prose-p:my-1 prose-ul:my-1 prose-li:my-0">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                </div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form
            onSubmit={handleSubmit}
            className="px-4 py-3 border-t border-gray-100 bg-white"
          >
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your question..."
                disabled={isLoading}
                className="flex-1 py-2.5 px-4 bg-gray-100 rounded-full text-sm outline-none focus:ring-2 focus:ring-[hsl(0,100%,45%)]/30 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="w-10 h-10 bg-[hsl(0,100%,45%)] rounded-full flex items-center justify-center text-white hover:bg-[hsl(0,100%,37%)] transition-colors disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ChatWidget;
