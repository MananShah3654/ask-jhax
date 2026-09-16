import { motion } from "framer-motion";
import { ChefHat, Sparkles, Globe } from "lucide-react";
import { Markdown } from "@/components/Markdown";

const SearchPill = ({ query, active }) => (
  <div className="inline-flex items-center gap-1.5 mb-2 px-2.5 py-1 rounded-full bg-[#EAF2FB] border border-[#CFE0F2] text-[11px] font-medium text-[#1D4E89]" data-testid="search-pill">
    <Globe size={12} className={active ? "jx-pulse-dot" : ""} />
    {active ? "Searching the web" : "Searched the web"}{query ? ` · ${query}` : ""}
  </div>
);

export default function MessageBubble({ msg, streaming }) {
  const isUser = msg.role === "user";
  const isSnapshot = msg.is_snapshot;

  if (isUser) {
    return (
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex justify-end" data-testid="user-message">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-[#B45309] text-white px-4 py-2.5 text-sm leading-relaxed shadow-sm">
          {msg.content}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex gap-3" data-testid={isSnapshot ? "snapshot-message" : "assistant-message"}>
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${isSnapshot ? "bg-[#2D251E]" : "bg-[#B45309]"}`}>
        <ChefHat size={17} className="text-white" />
      </div>
      <div className="flex-1 min-w-0">
        {isSnapshot ? (
          <div className="rounded-2xl border border-[#E4C892] bg-gradient-to-b from-[#FFFDF8] to-[#FBF4E6] p-5 shadow-[0_10px_40px_-16px_rgba(180,83,9,0.3)]">
            <div className="flex items-center gap-2 mb-3 pb-3 border-b border-[#EAD9B4]">
              <Sparkles size={14} className="text-[#B45309]" />
              <span className="text-[10px] uppercase tracking-[0.25em] font-semibold text-[#854D0E]">Restaurant Snapshot</span>
            </div>
            <Markdown>{msg.content || ""}</Markdown>
            {streaming && !msg.content && <ShimmerLines />}
            {streaming && msg.content && <span className="jx-cursor" />}
          </div>
        ) : (
          <div className="pt-1">
            {msg.searchStatus && <SearchPill query={msg.searchStatus} active={streaming && !msg.content} />}
            <Markdown>{msg.content || ""}</Markdown>
            {streaming && !msg.content && !msg.searchStatus && <ThinkingDots />}
            {streaming && msg.content && <span className="jx-cursor" />}
          </div>
        )}
      </div>
    </motion.div>
  );
}

const ThinkingDots = () => (
  <div className="flex items-center gap-1.5 py-1 text-[#8C7E72]">
    <span className="text-sm">jhax is thinking</span>
    <span className="flex gap-1">
      <span className="w-1.5 h-1.5 rounded-full bg-[#B45309] jx-pulse-dot" />
      <span className="w-1.5 h-1.5 rounded-full bg-[#B45309] jx-pulse-dot" style={{ animationDelay: "0.2s" }} />
      <span className="w-1.5 h-1.5 rounded-full bg-[#B45309] jx-pulse-dot" style={{ animationDelay: "0.4s" }} />
    </span>
  </div>
);

const ShimmerLines = () => (
  <div className="space-y-2.5">
    {[100, 92, 96, 70].map((w, i) => (
      <div key={i} className="h-3.5 rounded jx-shimmer" style={{ width: `${w}%` }} />
    ))}
  </div>
);
