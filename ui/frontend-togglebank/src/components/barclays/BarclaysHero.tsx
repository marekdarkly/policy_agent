import { Search, ArrowRight, Sparkles, ShieldCheck, Lock } from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";

const suggestedLinks = [
  "What are IBANs and SWIFT codes?",
  "I have a problem with a payment",
  "Find branch opening hours",
  "How do I find my sort code?",
  "How do I follow up on a complaint?",
];

const trustMarks = [
  "FDIC member",
  "256-bit encryption",
  "SOC 2 Type II",
  "FCA regulated",
  "ISO 27001",
];

interface BarclaysHeroProps {
  onSearch?: (query: string) => void;
}

const BarclaysHero = ({ onSearch }: BarclaysHeroProps) => {
  const [focused, setFocused] = useState(false);
  const [query, setQuery] = useState("");

  return (
    <section className="relative overflow-hidden bg-background">
      {/* Ambient mesh background --------------------------------------- */}
      <div className="mesh-bg" aria-hidden>
        <div
          className="mesh-orb orb-a"
          style={{
            top: "-10%",
            left: "-5%",
            width: 520,
            height: 520,
            background:
              "radial-gradient(circle at 30% 30%, hsl(var(--brand-accent) / .55), transparent 60%)",
          }}
        />
        <div
          className="mesh-orb orb-b"
          style={{
            top: "5%",
            right: "-8%",
            width: 600,
            height: 600,
            background:
              "radial-gradient(circle at 60% 40%, hsl(var(--brand-violet) / .45), transparent 60%)",
          }}
        />
        <div
          className="mesh-orb orb-c"
          style={{
            bottom: "-15%",
            left: "30%",
            width: 700,
            height: 700,
            background:
              "radial-gradient(circle at 50% 50%, hsl(var(--brand-gold) / .4), transparent 65%)",
          }}
        />
        {/* Soft top wash to keep header readable */}
        <div className="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-background to-transparent" />
        {/* Bottom fade into the next section */}
        <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-background to-transparent" />
      </div>

      {focused && (
        <div className="fixed inset-0 bg-foreground/15 backdrop-blur-[2px] z-30 pointer-events-none transition-opacity" />
      )}

      <div className="container relative z-40 pt-20 pb-10 md:pt-28 md:pb-14">
        {/* Eyebrow ----------------------------------------------------- */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.2, 0.8, 0.2, 1] }}
          className="flex justify-center mb-8"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-foreground/[0.04] border border-border/80 text-xs font-medium text-foreground/70">
            <Sparkles className="w-3.5 h-3.5 text-accent" />
            <span>Now with always-on AI support — answers in seconds</span>
            <ArrowRight className="w-3 h-3 opacity-50" />
          </div>
        </motion.div>

        {/* Headline ---------------------------------------------------- */}
        <motion.h1
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.2, 0.8, 0.2, 1] }}
          className="font-display text-5xl md:text-7xl lg:text-[88px] leading-[0.95] text-foreground text-center max-w-5xl mx-auto"
        >
          Banking, <em className="not-italic gradient-text">refined.</em>
          <br />
          Help, on demand.
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.1, ease: [0.2, 0.8, 0.2, 1] }}
          className="mt-6 text-base md:text-lg text-muted-foreground text-center max-w-xl mx-auto text-pretty"
        >
          Ask anything about your accounts, payments, mortgages, or fraud — our specialist
          team is here 24 / 7.
        </motion.p>

        {/* Search ------------------------------------------------------ */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.2, ease: [0.2, 0.8, 0.2, 1] }}
          className="mt-10 max-w-2xl mx-auto"
        >
          <div
            className={`relative rounded-2xl bg-card transition-all duration-300 ease-premium ${
              focused
                ? "shadow-elevated ring-1 ring-accent/40"
                : "shadow-card hover:shadow-card-hover"
            }`}
          >
            {/* Subtle gradient border highlight on focus */}
            <div
              className={`pointer-events-none absolute -inset-px rounded-2xl bg-gradient-to-r from-accent/0 via-accent/40 to-accent/0 opacity-0 transition-opacity ${
                focused ? "opacity-100" : ""
              }`}
              style={{ filter: "blur(8px)" }}
            />
            <div className="relative flex items-center">
              <Search className="ml-5 w-5 h-5 text-muted-foreground shrink-0" />
              <input
                type="text"
                placeholder="Ask a question, search help, or paste a payment reference…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && query.trim() && onSearch) onSearch(query.trim());
                }}
                className="flex-1 py-5 pl-3 pr-2 text-base bg-transparent rounded-2xl outline-none text-foreground placeholder:text-muted-foreground/80"
              />
              <button
                onClick={() => {
                  if (query.trim() && onSearch) onSearch(query.trim());
                }}
                className="m-1.5 bg-ink text-cream font-semibold text-sm px-5 py-3 rounded-xl hover:bg-ink-2 transition-colors inline-flex items-center gap-2 shadow-sm"
              >
                Ask
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Suggested chips ----------------------------------------- */}
          <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
            <span className="text-xs uppercase tracking-[0.18em] text-muted-foreground/80 font-medium mr-1">
              Try
            </span>
            {suggestedLinks.slice(0, 4).map((link) => (
              <button
                key={link}
                onClick={() => onSearch?.(link)}
                className="text-xs md:text-sm px-3 py-1.5 rounded-full bg-card border border-border hover:border-foreground/30 hover:bg-foreground/[0.02] text-foreground/80 hover:text-foreground transition-all"
              >
                {link}
              </button>
            ))}
          </div>
        </motion.div>

        {/* Trust strip ------------------------------------------------- */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.35, ease: [0.2, 0.8, 0.2, 1] }}
          className="mt-12 max-w-3xl mx-auto"
        >
          <div className="flex items-center justify-center gap-2 text-xs uppercase tracking-[0.2em] text-muted-foreground/80 font-medium mb-5">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Trusted by 12 million customers worldwide</span>
            <Lock className="w-3.5 h-3.5" />
          </div>
          <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-xs font-medium text-foreground/50">
            {trustMarks.map((m) => (
              <span key={m} className="inline-flex items-center gap-2">
                <span className="w-1 h-1 rounded-full bg-foreground/30" />
                {m}
              </span>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default BarclaysHero;
