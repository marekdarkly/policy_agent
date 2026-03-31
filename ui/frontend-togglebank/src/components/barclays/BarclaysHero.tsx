import { Search } from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";

const suggestedLinks = [
  "What are IBANs and SWIFT codes?",
  "I have a problem with a payment",
  "Find branch opening hours",
  "How do I find my sort code?",
  "How do I follow up on a complaint?",
];

interface BarclaysHeroProps {
  onSearch?: (query: string) => void;
}

const BarclaysHero = ({ onSearch }: BarclaysHeroProps) => {
  const [focused, setFocused] = useState(false);
  const [query, setQuery] = useState("");

  return (
    <section className="relative overflow-hidden">
      {/* Scenic background */}
      <div className="absolute inset-0 bg-gradient-to-b from-[hsl(var(--barclays-sky-light))] via-[hsl(var(--barclays-sky))] to-[hsl(var(--barclays-green))]" />
      {/* Treeline silhouette */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[hsl(var(--barclays-green-dark))]/40 to-transparent" />

      {focused && (
        <div className="fixed inset-0 bg-foreground/20 z-30 pointer-events-none" />
      )}

      <div className="container relative z-40 py-20 md:py-28 text-center">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.2, 0.8, 0.2, 1] }}
          className="text-3xl md:text-5xl font-bold text-white mb-8 tracking-tight drop-shadow-md"
        >
          How can we help you?
        </motion.h1>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15, ease: [0.2, 0.8, 0.2, 1] }}
          className="max-w-2xl mx-auto"
        >
          <div
            className={`relative bg-background rounded-lg shadow-card-hover transition-all duration-300 ease-premium ${
              focused ? "scale-[1.02] shadow-2xl" : ""
            }`}
          >
            <input
              type="text"
              placeholder="How can we help?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              className="w-full py-4 pl-6 pr-32 text-base md:text-lg bg-transparent rounded-lg outline-none text-foreground placeholder:text-muted-foreground"
            />
            <button
              onClick={() => { if (query.trim() && onSearch) onSearch(query.trim()); }}
              className="absolute right-2 top-1/2 -translate-y-1/2 bg-[hsl(var(--barclays-primary))] text-white font-semibold text-sm px-6 py-2.5 rounded-md hover:bg-[hsl(var(--barclays-dark))] transition-colors inline-flex items-center gap-2"
            >
              <Search className="w-4 h-4" />
              Search
            </button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3, ease: [0.2, 0.8, 0.2, 1] }}
          className="mt-8 max-w-2xl mx-auto text-left"
        >
          <p className="text-white/90 text-sm font-medium mb-3 drop-shadow-sm">
            Unsure what to search for? Other customers found these links helpful.
          </p>
          <ul className="space-y-1.5">
            {suggestedLinks.map((link) => (
              <li key={link}>
                <button
                  onClick={() => onSearch?.(link)}
                  className="text-white text-sm hover:underline transition-colors text-left flex items-center gap-2 group"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-white/60 group-hover:bg-white transition-colors shrink-0" />
                  {link}
                </button>
              </li>
            ))}
          </ul>
        </motion.div>
      </div>
    </section>
  );
};

export default BarclaysHero;
