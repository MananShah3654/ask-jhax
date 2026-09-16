import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ScanLine, MessageSquareText, CalendarClock, Users, Check, ChefHat } from "lucide-react";

const STEPS = [
  { icon: ScanLine, label: "Scraping current menu & pricing" },
  { icon: MessageSquareText, label: "Analyzing Google & Yelp review sentiment" },
  { icon: CalendarClock, label: "Checking local events & seasonal moments" },
  { icon: Users, label: "Running competitor benchmarking" },
];

export default function ResearchingState({ name }) {
  const [active, setActive] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setActive((a) => Math.min(a + 1, STEPS.length - 1)), 2600);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="min-h-screen bg-[#FAF8F5] flex items-center justify-center px-6">
      <div className="absolute inset-0 opacity-[0.4] pointer-events-none"
        style={{ backgroundImage: "radial-gradient(#E8DEC8 1px, transparent 1px)", backgroundSize: "22px 22px" }} />
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
        className="relative w-full max-w-md bg-white rounded-3xl border border-[#E8DEC8] p-8 shadow-[0_20px_60px_-20px_rgba(120,53,15,0.28)]">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 rounded-xl bg-[#B45309] flex items-center justify-center">
            <ChefHat size={20} className="text-white" />
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-[0.2em] font-semibold text-[#854D0E]">Getting up to speed</div>
            <div className="font-serif text-xl font-bold text-[#1E1B18] leading-tight">{name}</div>
          </div>
        </div>

        <div className="mt-6 space-y-1.5" data-testid="researching-state">
          {STEPS.map((s, i) => {
            const Icon = s.icon;
            const done = i < active;
            const current = i === active;
            return (
              <motion.div key={i} initial={{ opacity: 0.4 }} animate={{ opacity: done || current ? 1 : 0.4 }}
                className={`flex items-center gap-3 p-2.5 rounded-xl transition-colors duration-300 ${current ? "bg-[#F5EFE6]" : ""}`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors duration-300 ${
                  done ? "bg-[#15803D]" : current ? "bg-[#B45309]" : "bg-[#F4EFEA]"}`}>
                  {done ? <Check size={16} className="text-white" />
                    : <Icon size={16} className={current ? "text-white" : "text-[#B0A594]"} />}
                </div>
                <span className={`text-sm ${current ? "font-semibold text-[#1E1B18]" : done ? "text-[#574E46]" : "text-[#B0A594]"}`}>
                  {s.label}{current ? "…" : ""}
                </span>
                {current && (
                  <span className="ml-auto flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#B45309] jx-pulse-dot" />
                    <span className="w-1.5 h-1.5 rounded-full bg-[#B45309] jx-pulse-dot" style={{ animationDelay: "0.2s" }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-[#B45309] jx-pulse-dot" style={{ animationDelay: "0.4s" }} />
                  </span>
                )}
              </motion.div>
            );
          })}
        </div>
        <p className="mt-6 text-xs text-[#8C7E72] text-center">jhax is doing the homework so you don't have to.</p>
      </motion.div>
    </div>
  );
}
