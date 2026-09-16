import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { toast } from "sonner";

const DraftBox = ({ text }) => {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopied(false), 1800);
    } catch {
      toast.error("Copy failed");
    }
  };
  return (
    <div className="my-3 rounded-xl border border-[#E8DEC8] bg-[#2D251E] overflow-hidden" data-testid="draft-box">
      <div className="flex items-center justify-between px-3 py-2 bg-[#241d17] border-b border-[#3a2f24]">
        <span className="text-[10px] uppercase tracking-[0.2em] font-semibold text-[#D9A45B]">Draft · copy &amp; use</span>
        <button
          onClick={copy}
          data-testid="copy-draft-button"
          className="flex items-center gap-1.5 text-xs text-[#EADFCB] hover:text-white transition-colors duration-200"
        >
          {copied ? <Check size={13} /> : <Copy size={13} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="px-4 py-3 text-[13px] leading-relaxed text-[#F3E9D8] font-mono whitespace-pre-wrap break-words">{text}</pre>
    </div>
  );
};

export const Markdown = ({ children }) => (
  <div className="jx-prose">
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        pre({ children }) {
          const el = Array.isArray(children) ? children[0] : children;
          const raw = String(el?.props?.children ?? "").replace(/\n$/, "");
          return <DraftBox text={raw} />;
        },
        a({ node, ...props }) {
          return <a target="_blank" rel="noopener noreferrer" {...props} />;
        },
      }}
    >
      {children}
    </ReactMarkdown>
  </div>
);
