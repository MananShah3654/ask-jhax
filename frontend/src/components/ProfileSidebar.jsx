import { Star, Swords, CalendarClock, MessageSquareText, UtensilsCrossed, Info } from "lucide-react";

const sentimentColor = (s) => {
  const v = (s || "").toLowerCase();
  if (v.includes("neg")) return "text-[#B91C1C] bg-[#FBEAEA]";
  if (v.includes("pos")) return "text-[#15803D] bg-[#E8F3EC]";
  return "text-[#854D0E] bg-[#F5EFE6]";
};

const Section = ({ icon: Icon, title, children }) => (
  <div className="px-5 py-4 border-b border-[#E8DEC8] last:border-b-0">
    <div className="flex items-center gap-2 mb-3">
      <Icon size={14} className="text-[#B45309]" />
      <span className="text-[10px] uppercase tracking-[0.2em] font-semibold text-[#854D0E]">{title}</span>
    </div>
    {children}
  </div>
);

export default function ProfileSidebar({ restaurant: r }) {
  if (!r) return null;
  return (
    <div className="h-full overflow-y-auto no-scrollbar" data-testid="profile-sidebar">
      {/* header card */}
      <div className="px-5 py-5 border-b border-[#E8DEC8]">
        <h2 className="font-serif text-2xl font-bold text-[#1E1B18] leading-tight">{r.name}</h2>
        {r.location && <div className="text-sm text-[#8C7E72] mt-0.5">{r.location}</div>}
        <div className="flex flex-wrap items-center gap-2 mt-3">
          {r.cuisine && <span className="text-xs font-semibold text-[#78350F] bg-[#F5EFE6] px-2.5 py-1 rounded-full">{r.cuisine}</span>}
          {r.price_tier && <span className="text-xs font-mono font-semibold text-white bg-[#2D251E] px-2.5 py-1 rounded-full">{r.price_tier}</span>}
          {r.rating != null && (
            <span className="flex items-center gap-1 text-xs font-mono font-semibold text-[#B45309] bg-white border border-[#E8DEC8] px-2.5 py-1 rounded-full">
              <Star size={12} className="fill-[#D97706] text-[#D97706]" /> {r.rating}
            </span>
          )}
        </div>
        {r.positioning && <p className="mt-3 text-sm text-[#574E46] leading-relaxed">{r.positioning}</p>}
        {r.vibe && <p className="mt-1.5 text-xs italic text-[#8C7E72]">“{r.vibe}”</p>}
      </div>

      {r.competitors?.length > 0 && (
        <Section icon={Swords} title="Direct Competitors">
          <div className="space-y-2.5">
            {r.competitors.map((c, i) => (
              <div key={i} className="text-sm">
                <div className="font-semibold text-[#1E1B18]">{c.name}</div>
                {c.note && <div className="text-xs text-[#8C7E72] leading-snug mt-0.5">{c.note}</div>}
              </div>
            ))}
          </div>
        </Section>
      )}

      {r.local_context?.length > 0 && (
        <Section icon={CalendarClock} title="Happening Nearby">
          <div className="space-y-2.5">
            {r.local_context.map((e, i) => (
              <div key={i} className="text-sm">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-semibold text-[#1E1B18]">{e.title}</span>
                  {e.when && <span className="text-[10px] font-mono text-[#B45309] whitespace-nowrap">{e.when}</span>}
                </div>
                {e.impact && <div className="text-xs text-[#8C7E72] leading-snug mt-0.5">{e.impact}</div>}
              </div>
            ))}
          </div>
        </Section>
      )}

      {r.review_themes?.length > 0 && (
        <Section icon={MessageSquareText} title="Review Themes">
          <div className="space-y-2">
            {r.review_themes.map((t, i) => (
              <div key={i}>
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${sentimentColor(t.sentiment)}`}>{t.sentiment}</span>
                  <span className="text-sm font-medium text-[#1E1B18]">{t.theme}</span>
                </div>
                {t.note && <div className="text-xs text-[#8C7E72] leading-snug mt-0.5 ml-1">{t.note}</div>}
              </div>
            ))}
          </div>
        </Section>
      )}

      {r.menu_data?.length > 0 && (
        <Section icon={UtensilsCrossed} title="Menu Snapshot">
          <div className="space-y-3">
            {r.menu_data.slice(0, 4).map((sec, i) => (
              <div key={i}>
                <div className="text-xs font-semibold text-[#78350F] mb-1">{sec.section}</div>
                <div className="space-y-1">
                  {(sec.items || []).slice(0, 5).map((it, j) => (
                    <div key={j} className="flex items-baseline justify-between gap-3 text-sm">
                      <span className="text-[#574E46]">{it.name}</span>
                      {it.price && <span className="font-mono text-xs text-[#1E1B18]">${String(it.price).replace(/^\$/, "")}</span>}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {r.data_confidence && (
        <div className="px-5 py-4 flex items-start gap-2 bg-[#F5EFE6]">
          <Info size={13} className="text-[#854D0E] mt-0.5 flex-shrink-0" />
          <p className="text-xs text-[#574E46] leading-snug"><span className="font-semibold">Data confidence:</span> {r.data_confidence}</p>
        </div>
      )}
    </div>
  );
}
