import { useEffect, useRef } from "react";
import { Send, TrendingDown, CalendarRange, Tag, Users, Instagram } from "lucide-react";
import MessageBubble from "@/components/MessageBubble";

const CHIPS = [
  { icon: TrendingDown, label: "Cut my prime cost 3%", p: "How can I bring my prime cost down by 3% without hurting quality or the guest experience?" },
  { icon: CalendarRange, label: "Weekend promo ideas", p: "Give me 3-5 weekend promotion ideas tailored to my restaurant, then tell me which one you'd run first and why." },
  { icon: Tag, label: "Re-price my menu", p: "Where should I re-price my menu? Point out items that are underpriced or dragging margin and suggest new prices." },
  { icon: Instagram, label: "Friday caption", p: "Draft an Instagram caption for this Friday's chef special. Give me 3 options with different vibes." },
  { icon: Users, label: "Staff incentive plan", p: "Give me a 5-step staff incentive plan to improve service speed and retention." },
];

export default function ChatPanel({ messages, streaming, input, setInput, onSend, restaurantName }) {
  const endRef = useRef(null);
  const taRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming]);

  const submit = (e) => {
    e.preventDefault();
    if (!input.trim() || streaming) return;
    onSend(input.trim());
  };

  const handleChip = (p) => { if (!streaming) onSend(p); };

  return (
    <div className="flex flex-col h-full">
      {/* messages */}
      <div className="flex-1 overflow-y-auto no-scrollbar px-4 sm:px-6 lg:px-8 py-6" data-testid="chat-messages">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((m) => (
            <MessageBubble key={m.id} msg={m} streaming={streaming && m.id === "streaming"} />
          ))}
          <div ref={endRef} />
        </div>
      </div>

      {/* composer */}
      <div className="border-t border-[#E8DEC8] bg-[#FAF8F5]/95 backdrop-blur-md px-4 sm:px-6 lg:px-8 pt-3 pb-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex gap-2 overflow-x-auto no-scrollbar pb-2.5 -mx-1 px-1">
            {CHIPS.map((c) => {
              const Icon = c.icon;
              return (
                <button key={c.label} onClick={() => handleChip(c.p)} data-testid="prompt-chip" disabled={streaming}
                  className="flex items-center gap-1.5 whitespace-nowrap px-3 py-1.5 rounded-full bg-white border border-[#E8DEC8] text-xs font-medium text-[#574E46] hover:border-[#B45309] hover:text-[#78350F] disabled:opacity-50 transition-colors duration-200 flex-shrink-0">
                  <Icon size={13} className="text-[#B45309]" /> {c.label}
                </button>
              );
            })}
          </div>
          <form onSubmit={submit} className="flex items-end gap-2 bg-white rounded-2xl border border-[#E8DEC8] p-2 focus-within:border-[#B45309] focus-within:ring-2 focus-within:ring-[#B45309]/15 transition-all">
            <textarea
              ref={taRef}
              data-testid="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) submit(e); }}
              rows={1}
              placeholder={`Ask jhax anything about ${restaurantName}…`}
              className="flex-1 resize-none bg-transparent px-3 py-2 text-sm text-[#1E1B18] placeholder-[#B0A594] focus:outline-none max-h-32"
            />
            <button type="submit" disabled={!input.trim() || streaming} data-testid="chat-send-button"
              className="w-10 h-10 rounded-xl bg-[#B45309] hover:bg-[#92400E] active:bg-[#78350F] disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center justify-center transition-colors duration-200 flex-shrink-0">
              <Send size={17} />
            </button>
          </form>
          <p className="text-[11px] text-[#B0A594] text-center mt-2">jhax reasons from live web research — verify critical numbers before acting.</p>
        </div>
      </div>
    </div>
  );
}
