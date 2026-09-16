import { useState } from "react";
import { Calculator, Grid2x2, PenLine, TrendingDown, TrendingUp } from "lucide-react";

const Field = ({ label, value, onChange, suffix }) => (
  <div>
    <label className="block text-xs font-medium text-[#574E46] mb-1">{label}</label>
    <div className="relative">
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 rounded-lg bg-[#FAF8F5] border border-[#E8DEC8] text-sm font-mono text-[#1E1B18] focus:outline-none focus:border-[#B45309] transition-colors"
      />
      {suffix && <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[#8C7E72] font-mono">{suffix}</span>}
    </div>
  </div>
);

const PrimeCostCalculator = () => {
  const [sales, setSales] = useState(100000);
  const [food, setFood] = useState(30000);
  const [labor, setLabor] = useState(32000);
  const s = Number(sales) || 0;
  const foodPct = s ? (Number(food) / s) * 100 : 0;
  const laborPct = s ? (Number(labor) / s) * 100 : 0;
  const prime = foodPct + laborPct;
  const status = prime <= 60 ? { c: "#15803D", t: "Healthy — you're under the 60% benchmark." }
    : prime <= 65 ? { c: "#B45309", t: "Watch it — trim toward 60% to protect margin." }
      : { c: "#B91C1C", t: "Too high — prime cost is eating your profit." };
  return (
    <div className="space-y-3">
      <Field label="Monthly sales" value={sales} onChange={setSales} suffix="$" />
      <div className="grid grid-cols-2 gap-3">
        <Field label="Food + bev cost" value={food} onChange={setFood} suffix="$" />
        <Field label="Labor cost" value={labor} onChange={setLabor} suffix="$" />
      </div>
      <div className="rounded-xl border border-[#E8DEC8] bg-white p-4 mt-1">
        <div className="flex items-end justify-between">
          <span className="text-xs uppercase tracking-[0.15em] font-semibold text-[#854D0E]">Prime Cost</span>
          <span className="font-mono text-3xl font-bold" style={{ color: status.c }} data-testid="prime-cost-result">{prime.toFixed(1)}%</span>
        </div>
        <div className="h-2 rounded-full bg-[#F4EFEA] mt-2 overflow-hidden">
          <div className="h-full rounded-full transition-all duration-300" style={{ width: `${Math.min(prime, 100)}%`, background: status.c }} />
        </div>
        <div className="flex justify-between text-[11px] font-mono text-[#8C7E72] mt-2">
          <span>Food {foodPct.toFixed(1)}%</span>
          <span>Labor {laborPct.toFixed(1)}%</span>
        </div>
        <p className="text-xs mt-2 leading-snug" style={{ color: status.c }}>{status.t}</p>
      </div>
    </div>
  );
};

const MATRIX = [
  { q: "Star", d: "High margin · high popularity", note: "Feature loudly, protect the recipe.", up: true, color: "#15803D" },
  { q: "Plowhorse", d: "Low margin · high popularity", note: "Re-engineer cost or nudge price up.", up: false, color: "#B45309" },
  { q: "Puzzle", d: "High margin · low popularity", note: "Reposition, rename, or push on specials.", up: true, color: "#D97706" },
  { q: "Dog", d: "Low margin · low popularity", note: "Cut it unless it's strategic.", up: false, color: "#B91C1C" },
];

export default function ToolsPanel({ onQuickPrompt }) {
  const [tab, setTab] = useState("prime");
  const tabs = [
    { id: "prime", label: "Prime Cost", icon: Calculator },
    { id: "menu", label: "Menu Matrix", icon: Grid2x2 },
    { id: "caption", label: "Studio", icon: PenLine },
  ];
  return (
    <div className="h-full overflow-y-auto no-scrollbar" data-testid="tools-panel">
      <div className="sticky top-0 bg-[#F4EFEA] px-3 pt-4 pb-3 z-10">
        <div className="text-[10px] uppercase tracking-[0.2em] font-semibold text-[#854D0E] mb-3 px-1">Execution Tools</div>
        <div className="flex gap-1 bg-white rounded-xl p-1 border border-[#E8DEC8]">
          {tabs.map((t) => {
            const Icon = t.icon;
            return (
              <button key={t.id} onClick={() => setTab(t.id)} data-testid={`tool-tab-${t.id}`}
                className={`flex-1 flex flex-col items-center gap-1 py-2 rounded-lg text-[11px] font-semibold transition-colors duration-200 ${
                  tab === t.id ? "bg-[#B45309] text-white" : "text-[#8C7E72] hover:text-[#1E1B18]"}`}>
                <Icon size={15} /> {t.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="px-4 py-4">
        {tab === "prime" && <PrimeCostCalculator />}

        {tab === "menu" && (
          <div className="space-y-2.5">
            <p className="text-xs text-[#574E46] leading-relaxed mb-1">Classify every dish, then act on the quadrant:</p>
            {MATRIX.map((m) => (
              <div key={m.q} className="rounded-xl border border-[#E8DEC8] bg-white p-3">
                <div className="flex items-center gap-2">
                  {m.up ? <TrendingUp size={15} style={{ color: m.color }} /> : <TrendingDown size={15} style={{ color: m.color }} />}
                  <span className="font-serif font-semibold text-[#1E1B18]">{m.q}</span>
                  <span className="ml-auto text-[10px] font-mono text-[#8C7E72]">{m.d}</span>
                </div>
                <p className="text-xs text-[#574E46] mt-1.5 leading-snug">{m.note}</p>
              </div>
            ))}
            <button onClick={() => onQuickPrompt("Run a menu engineering analysis on my menu — classify my top items as Star, Plowhorse, Puzzle or Dog and tell me what to do with each.")}
              className="w-full mt-1 py-2.5 rounded-lg bg-[#2D251E] hover:bg-[#1E1B18] text-white text-sm font-semibold transition-colors duration-200">
              Ask jhax to run this on my menu
            </button>
          </div>
        )}

        {tab === "caption" && (
          <div className="space-y-2.5">
            <p className="text-xs text-[#574E46] leading-relaxed mb-1">Get copy-paste-ready drafts in seconds:</p>
            {[
              { t: "Instagram caption", p: "Write me a punchy Instagram caption for this Friday's chef special. Give me 3 options with different vibes." },
              { t: "WhatsApp broadcast", p: "Draft a WhatsApp broadcast to my regulars about a weekend promotion. Keep it warm and short." },
              { t: "Specials-board line", p: "Give me 5 short, mouth-watering specials-board lines I can chalk up today." },
              { t: "Google review reply", p: "Draft a gracious reply to a 3-star Google review that complained about slow service." },
            ].map((c) => (
              <button key={c.t} onClick={() => onQuickPrompt(c.p)} data-testid="studio-prompt"
                className="w-full text-left p-3 rounded-xl border border-[#E8DEC8] bg-white hover:border-[#B45309] transition-colors duration-200">
                <div className="text-sm font-semibold text-[#1E1B18]">{c.t}</div>
                <div className="text-xs text-[#8C7E72] mt-0.5 line-clamp-1">{c.p}</div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
