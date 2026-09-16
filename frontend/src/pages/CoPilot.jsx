import { useState, useCallback } from "react";
import { ChefHat, MapPin, PanelRightOpen, PanelRightClose, RotateCcw, Menu, Radio } from "lucide-react";
import { toast } from "sonner";
import Landing from "@/components/Landing";
import ResearchingState from "@/components/ResearchingState";
import ProfileSidebar from "@/components/ProfileSidebar";
import ToolsPanel from "@/components/ToolsPanel";
import ChatPanel from "@/components/ChatPanel";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { researchRestaurant, streamEndpoint } from "@/lib/api";

let msgCounter = 0;
const newId = () => `m_${Date.now()}_${msgCounter++}`;

export default function CoPilot() {
  const [view, setView] = useState("landing");
  const [researchName, setResearchName] = useState("");
  const [restaurant, setRestaurant] = useState(null);
  const [messages, setMessages] = useState([]);
  const [streaming, setStreaming] = useState(false);
  const [input, setInput] = useState("");
  const [showTools, setShowTools] = useState(false);

  const appendDelta = useCallback((chunk) => {
    setMessages((prev) => prev.map((m) => (m.id === "streaming" ? { ...m, content: m.content + chunk } : m)));
  }, []);

  const handleTool = useCallback((evt) => {
    setMessages((prev) => prev.map((m) => (m.id === "streaming" ? { ...m, searchStatus: evt.query || "the web" } : m)));
  }, []);

  const finalize = useCallback(() => {
    setMessages((prev) => prev.map((m) => (m.id === "streaming" ? { ...m, id: newId() } : m)));
    setStreaming(false);
  }, []);

  const runSnapshot = useCallback((rid) => {
    setStreaming(true);
    setMessages([{ id: "streaming", role: "assistant", content: "", is_snapshot: true }]);
    streamEndpoint(
      `/restaurants/${rid}/snapshot/stream`, {},
      appendDelta, finalize,
      (err) => { toast.error("Couldn't load snapshot"); finalize(); }
    );
  }, [appendDelta, finalize]);

  const handleStart = useCallback(async (payload) => {
    setResearchName(payload.name);
    setView("researching");
    try {
      const r = await researchRestaurant(payload);
      setRestaurant(r);
      setView("chat");
      runSnapshot(r.id);
    } catch (e) {
      toast.error("Research failed — try again.");
      setView("landing");
    }
  }, [runSnapshot]);

  const handleSend = useCallback((text) => {
    if (!restaurant || streaming) return;
    setInput("");
    setMessages((prev) => [
      ...prev,
      { id: newId(), role: "user", content: text },
      { id: "streaming", role: "assistant", content: "" },
    ]);
    setStreaming(true);
    streamEndpoint(
      `/restaurants/${restaurant.id}/chat/stream`, { message: text },
      appendDelta, finalize,
      (err) => { toast.error("Message failed"); finalize(); },
      handleTool
    );
  }, [restaurant, streaming, appendDelta, finalize, handleTool]);

  const handleReset = () => {
    setView("landing");
    setRestaurant(null);
    setMessages([]);
    setInput("");
    setShowTools(false);
  };

  if (view === "landing") return <Landing onStart={handleStart} />;
  if (view === "researching") return <ResearchingState name={researchName} />;

  return (
    <div className="h-screen flex flex-col bg-[#FAF8F5] overflow-hidden">
      {/* header */}
      <header className="sticky top-0 z-30 flex items-center gap-3 px-4 sm:px-5 h-16 bg-[#FAF8F5]/90 backdrop-blur-md border-b border-[#E8DEC8]">
        {/* mobile profile trigger */}
        <div className="lg:hidden">
          <Sheet>
            <SheetTrigger asChild>
              <button data-testid="mobile-profile-trigger" className="w-9 h-9 rounded-lg border border-[#E8DEC8] bg-white flex items-center justify-center text-[#574E46]">
                <Menu size={18} />
              </button>
            </SheetTrigger>
            <SheetContent side="left" className="w-[320px] p-0 bg-[#F4EFEA]">
              <ProfileSidebar restaurant={restaurant} />
            </SheetContent>
          </Sheet>
        </div>

        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#B45309] flex items-center justify-center">
            <ChefHat size={18} className="text-white" />
          </div>
          <span className="font-bold tracking-tight text-[#1E1B18] hidden sm:inline">jhax<span className="text-[#B45309]">.ai</span></span>
        </div>

        <div className="h-6 w-px bg-[#E8DEC8] hidden sm:block" />

        <div className="flex-1 min-w-0">
          <div className="font-serif text-lg font-bold text-[#1E1B18] leading-none truncate">{restaurant?.name}</div>
          {restaurant?.location && (
            <div className="flex items-center gap-1 text-xs text-[#8C7E72] mt-0.5">
              <MapPin size={11} /> <span className="truncate">{restaurant.location}</span>
            </div>
          )}
        </div>

        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#E8F3EC] border border-[#C7E3D0]">
          <Radio size={12} className="text-[#15803D] jx-pulse-dot" />
          <span className="text-[11px] font-semibold text-[#15803D]">Live market data</span>
        </div>

        <button onClick={() => setShowTools((s) => !s)} data-testid="toggle-tools-button"
          className="hidden lg:flex items-center gap-1.5 px-3 h-9 rounded-lg border border-[#E8DEC8] bg-white text-sm font-medium text-[#574E46] hover:border-[#B45309] hover:text-[#78350F] transition-colors duration-200">
          {showTools ? <PanelRightClose size={16} /> : <PanelRightOpen size={16} />}
          Tools
        </button>

        {/* mobile tools trigger */}
        <div className="lg:hidden">
          <Sheet>
            <SheetTrigger asChild>
              <button data-testid="mobile-tools-trigger" className="w-9 h-9 rounded-lg border border-[#E8DEC8] bg-white flex items-center justify-center text-[#574E46]">
                <PanelRightOpen size={18} />
              </button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[330px] p-0 bg-[#F4EFEA]">
              <ToolsPanel onQuickPrompt={(p) => handleSend(p)} />
            </SheetContent>
          </Sheet>
        </div>

        <button onClick={handleReset} data-testid="reset-button"
          className="w-9 h-9 rounded-lg border border-[#E8DEC8] bg-white flex items-center justify-center text-[#574E46] hover:border-[#B45309] hover:text-[#78350F] transition-colors duration-200" title="New restaurant">
          <RotateCcw size={16} />
        </button>
      </header>

      {/* body */}
      <div className="flex-1 flex overflow-hidden">
        <aside className="hidden lg:block w-[320px] flex-shrink-0 bg-[#F4EFEA] border-r border-[#E8DEC8]">
          <ProfileSidebar restaurant={restaurant} />
        </aside>

        <main className="flex-1 min-w-0">
          <ChatPanel
            messages={messages}
            streaming={streaming}
            input={input}
            setInput={setInput}
            onSend={handleSend}
            restaurantName={restaurant?.name}
          />
        </main>

        {showTools && (
          <aside className="hidden lg:block w-[330px] flex-shrink-0 bg-[#F4EFEA] border-l border-[#E8DEC8] jx-fade-up">
            <ToolsPanel onQuickPrompt={(p) => { handleSend(p); }} />
          </aside>
        )}
      </div>
    </div>
  );
}
