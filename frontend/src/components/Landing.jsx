import { useState } from "react";
import { motion } from "framer-motion";
import { ChefHat, MapPin, Sparkles, ArrowRight, Utensils } from "lucide-react";

const SAMPLES = [
  { name: "Osteria Rustica", location: "North End, Boston", cuisine: "Italian Fine Casual", tag: "Italian · $$$", img: "https://images.unsplash.com/photo-1774979517545-1897d30b5d27?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1Mjh8MHwxfHNlYXJjaHszfHxjb3p5JTIwbHV4dXJ5JTIwcmVzdGF1cmFudCUyMGludGVyaW9yJTIwZGluaW5nJTIwY2hlZiUyMGNyYWZ0JTIwZm9vZHxlbnwwfHx8fDE3ODk1NjAyNzB8MA&ixlib=rb-4.1.0&q=85" },
  { name: "The Smoked Barrel", location: "Austin, TX", cuisine: "BBQ & Craft Taphouse", tag: "BBQ · $$", img: "https://images.unsplash.com/photo-1645492884526-654081e772de?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1Mjh8MHwxfHNlYXJjaHwxfHxjb3p5JTIwbHV4dXJ5JTIwcmVzdGF1cmFudCUyMGludGVyaW9yJTIwZGluaW5nJTIwY2hlZiUyMGNyYWZ0JTIwZm9vZHxlbnwwfHx8fDE3ODk1NjAyNzB8MA&ixlib=rb-4.1.0&q=85" },
  { name: "Green Sprout", location: "Portland, OR", cuisine: "Plant-based Fast Casual", tag: "Vegan · $$", img: "https://images.unsplash.com/photo-1572715376701-98568319fd0b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwxfHxnb3VybWV0JTIwZm9vZCUyMGNoZWYlMjBwbGF0aW5nJTIwc3RlYWslMjBwYXN0YSUyMGJpc3Ryb3xlbnwwfHx8fDE3ODk1NjAyNzd8MA&ixlib=rb-4.1.0&q=85" },
];

export default function Landing({ onStart }) {
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [cuisine, setCuisine] = useState("");

  const submit = (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    onStart({ name: name.trim(), location: location.trim(), cuisine: cuisine.trim() });
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] relative overflow-hidden">
      <div className="absolute inset-0 opacity-[0.4] pointer-events-none"
        style={{ backgroundImage: "radial-gradient(#E8DEC8 1px, transparent 1px)", backgroundSize: "22px 22px" }} />
      <div className="relative max-w-6xl mx-auto px-6 py-14 lg:py-20">
        {/* brand */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2.5 mb-14">
          <div className="w-9 h-9 rounded-lg bg-[#B45309] flex items-center justify-center shadow-sm">
            <ChefHat size={20} className="text-[#FAF8F5]" />
          </div>
          <span className="text-xl font-bold tracking-tight text-[#1E1B18]">jhax<span className="text-[#B45309]">.ai</span></span>
          <span className="ml-2 text-[10px] uppercase tracking-[0.2em] font-semibold text-[#854D0E] hidden sm:inline">Restaurant Co-Pilot</span>
        </motion.div>

        <div className="grid lg:grid-cols-[1.1fr_0.9fr] gap-12 lg:gap-16 items-center">
          {/* left copy + form */}
          <div>
            <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F5EFE6] border border-[#E8DEC8] mb-6">
              <Sparkles size={13} className="text-[#B45309]" />
              <span className="text-xs font-semibold text-[#78350F]">A 15-year restaurant COO, on demand</span>
            </motion.div>

            <motion.h1 initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
              className="font-serif text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-[#1E1B18] leading-[1.02]">
              Your restaurant,<br />already <span className="text-[#B45309] italic">figured out</span>.
            </motion.h1>

            <motion.p initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
              className="mt-5 text-base sm:text-lg text-[#574E46] max-w-lg leading-relaxed">
              Drop in your restaurant name. jhax researches your menu, competitors, reviews and what's
              happening in your neighborhood this week — then opens with a snapshot that proves it already gets your business.
            </motion.p>

            <motion.form initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
              onSubmit={submit} className="mt-8 bg-white rounded-2xl border border-[#E8DEC8] p-5 shadow-[0_8px_30px_-12px_rgba(120,53,15,0.18)]">
              <label className="block text-[10px] uppercase tracking-[0.2em] font-semibold text-[#854D0E] mb-1.5">Restaurant name</label>
              <div className="relative mb-3">
                <Utensils size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#B45309]" />
                <input
                  data-testid="search-restaurant-input"
                  value={name} onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Osteria Rustica"
                  className="w-full pl-9 pr-3 py-3 rounded-xl bg-[#FAF8F5] border border-[#E8DEC8] text-[#1E1B18] placeholder-[#B0A594] focus:outline-none focus:border-[#B45309] focus:ring-2 focus:ring-[#B45309]/15 transition-all"
                />
              </div>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="relative">
                  <MapPin size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8C7E72]" />
                  <input
                    data-testid="restaurant-location-input"
                    value={location} onChange={(e) => setLocation(e.target.value)}
                    placeholder="City / neighborhood"
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-[#FAF8F5] border border-[#E8DEC8] text-sm text-[#1E1B18] placeholder-[#B0A594] focus:outline-none focus:border-[#B45309] transition-all"
                  />
                </div>
                <input
                  data-testid="restaurant-cuisine-input"
                  value={cuisine} onChange={(e) => setCuisine(e.target.value)}
                  placeholder="Cuisine (optional)"
                  className="w-full px-3 py-2.5 rounded-xl bg-[#FAF8F5] border border-[#E8DEC8] text-sm text-[#1E1B18] placeholder-[#B0A594] focus:outline-none focus:border-[#B45309] transition-all"
                />
              </div>
              <button
                type="submit"
                data-testid="start-copilot-button"
                disabled={!name.trim()}
                className="group w-full flex items-center justify-center gap-2 py-3.5 rounded-xl bg-[#B45309] hover:bg-[#92400E] active:bg-[#78350F] disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold transition-colors duration-200"
              >
                Bring jhax up to speed
                <ArrowRight size={17} className="group-hover:translate-x-0.5 transition-transform duration-200" />
              </button>
            </motion.form>
          </div>

          {/* right: sample picks */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
            <p className="text-[10px] uppercase tracking-[0.2em] font-semibold text-[#854D0E] mb-4">Or try a benchmark restaurant</p>
            <div className="space-y-3">
              {SAMPLES.map((s, i) => (
                <button
                  key={s.name}
                  data-testid="restaurant-select-option"
                  onClick={() => onStart(s)}
                  className="group w-full flex items-center gap-4 p-3 rounded-2xl bg-white border border-[#E8DEC8] hover:border-[#B45309] hover:shadow-[0_10px_30px_-14px_rgba(120,53,15,0.35)] transition-all duration-200 text-left"
                >
                  <div className="w-16 h-16 rounded-xl overflow-hidden flex-shrink-0 bg-[#F5EFE6]">
                    <img src={s.img} alt={s.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-serif text-lg font-semibold text-[#1E1B18] leading-tight">{s.name}</div>
                    <div className="flex items-center gap-1.5 text-xs text-[#8C7E72] mt-0.5">
                      <MapPin size={12} /> {s.location}
                    </div>
                    <span className="inline-block mt-1.5 text-[10px] font-mono font-semibold text-[#78350F] bg-[#F5EFE6] px-2 py-0.5 rounded-full">{s.tag}</span>
                  </div>
                  <ArrowRight size={18} className="text-[#D4C5A9] group-hover:text-[#B45309] group-hover:translate-x-0.5 transition-all duration-200" />
                </button>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
