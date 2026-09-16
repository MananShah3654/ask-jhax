import { useState } from "react";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Play, ArrowUpRight, Sparkles } from "lucide-react";

const DEMO = [
  { g: "Prove it knows me", q: "(Let the Snapshot auto-open — this is the opener)", note: "Auto-generated. Nothing to type — it already knows the business.", disabled: true },
  { g: "Live data", q: "Who are my real competitors nearby and how do I beat each one?" },
  { g: "Live data", q: "What are my current business hours and are they consistent everywhere?" },
  { g: "Ready-to-use", q: "Draft me an Instagram caption for this Friday's special — give me 3 vibes." },
  { g: "Works in constraints", q: "I have $200 and 3 days — get me more weekend covers." },
  { g: "Consultant frameworks", q: "Run a menu-engineering analysis — which items are Stars, Plowhorses, Puzzles, Dogs?" },
  { g: "Honest, not a hype bot", q: "My chef wants to add a $32 short rib. Good idea?" },
  { g: "Proactive", q: "What's happening in my area in the next 2 weeks I can cash in on?" },
  { g: "Ready-to-use", q: "Write a WhatsApp broadcast to bring my regulars back this week." },
  { g: "Strategy + tools", q: "Give me a 5-step plan to cut my prime cost 3% without hurting quality." },
];

export default function DemoSheet({ onSend, disabled }) {
  const [open, setOpen] = useState(false);
  const pick = (q) => { setOpen(false); setTimeout(() => onSend(q), 150); };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <button data-testid="demo-script-button"
          className="flex items-center gap-1.5 px-3 h-9 rounded-lg bg-[#2D251E] text-sm font-medium text-white hover:bg-[#1E1B18] transition-colors duration-200">
          <Play size={15} className="fill-white" /> <span className="hidden sm:inline">Demo</span>
        </button>
      </SheetTrigger>
      <SheetContent side="right" className="w-[380px] p-0 bg-[#FAF8F5] overflow-y-auto no-scrollbar">
        <SheetHeader className="px-5 pt-5 pb-3 border-b border-[#E8DEC8]">
          <SheetTitle className="flex items-center gap-2 font-serif text-2xl text-[#1E1B18]">
            <Sparkles size={18} className="text-[#B45309]" /> Soft-Launch Script
          </SheetTitle>
          <p className="text-xs text-[#8C7E72] text-left">Tap any question to fire it into the chat. Ordered for maximum "aha".</p>
        </SheetHeader>
        <div className="p-4 space-y-2.5">
          {DEMO.map((d, i) => (
            <button key={i} disabled={disabled || d.disabled}
              onClick={() => !d.disabled && pick(d.q)}
              data-testid="demo-question"
              className={`group w-full text-left p-3.5 rounded-xl border transition-all duration-200 ${
                d.disabled
                  ? "border-dashed border-[#D4C5A9] bg-[#F5EFE6] cursor-default"
                  : "border-[#E8DEC8] bg-white hover:border-[#B45309] hover:shadow-[0_8px_24px_-14px_rgba(120,53,15,0.35)]"} disabled:opacity-60`}>
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-[#B45309] text-white text-[11px] font-bold flex items-center justify-center flex-shrink-0">{i + 1}</span>
                  <span className="text-[10px] uppercase tracking-[0.15em] font-semibold text-[#854D0E]">{d.g}</span>
                </span>
                {!d.disabled && <ArrowUpRight size={15} className="text-[#D4C5A9] group-hover:text-[#B45309] transition-colors" />}
              </div>
              <div className="text-sm font-medium text-[#1E1B18] leading-snug">{d.q}</div>
              {d.note && <div className="text-xs text-[#8C7E72] mt-1 italic">{d.note}</div>}
            </button>
          ))}
        </div>
      </SheetContent>
    </Sheet>
  );
}
