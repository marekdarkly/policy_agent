import { Search, Sparkles, ChevronRight } from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";

const quickLinks = [
  "How can I fix my slow broadband?",
  "How do I activate my new SIM?",
  "How do I view my bill online?",
];

interface HeroSearchProps {
  onSearch: (query: string) => void;
}

const HeroSearch = ({ onSearch }: HeroSearchProps) => {
  const [focused, setFocused] = useState(false);
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
      setQuery("");
    }
  };

  return (
    <section className="relative bg-primary overflow-hidden">
      {focused && (
        <div className="fixed inset-0 bg-foreground/20 z-30 pointer-events-none" />
      )}

      <div className="container relative z-40 py-16 md:py-24 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.2, 0.8, 0.2, 1] }}
        >
          <h1 className="text-3xl md:text-5xl font-bold text-primary-foreground mb-3 tracking-tight">
            Help and Support
          </h1>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1, ease: [0.2, 0.8, 0.2, 1] }}
          className="mb-3"
        >
          <Sparkles className="w-10 h-10 text-primary-foreground/80 mx-auto mb-3" />
          <h2 className="text-xl md:text-2xl font-semibold text-primary-foreground mb-2">
            Need help? Ask a question.
          </h2>
          <p className="text-primary-foreground/80 text-sm md:text-base">
            The more detail you provide, the better we can help you.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scaleX: 0.8 }}
          animate={{ opacity: 1, scaleX: 1 }}
          transition={{ duration: 0.5, delay: 0.2, ease: [0.2, 0.8, 0.2, 1] }}
          className="max-w-2xl mx-auto mt-8"
        >
          <form onSubmit={handleSubmit}>
            <div
              className={`relative bg-background rounded-pill shadow-card-hover transition-all duration-300 ease-premium ${
                focused ? "scale-[1.02] shadow-2xl" : ""
              }`}
            >
              <input
                type="text"
                placeholder="Ask anything..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                className="w-full py-4 pl-6 pr-14 text-base md:text-lg bg-transparent rounded-pill outline-none text-foreground placeholder:text-muted-foreground"
              />
              <button
                type="submit"
                className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 bg-primary rounded-full flex items-center justify-center hover:bg-primary-hover transition-colors"
              >
                <Search className="w-5 h-5 text-primary-foreground" />
              </button>
            </div>
          </form>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
          className="flex flex-col sm:flex-row gap-3 justify-center mt-8"
        >
          {quickLinks.map((link) => (
            <button
              key={link}
              onClick={() => onSearch(link)}
              className="group flex items-center gap-2 bg-primary-foreground/10 hover:bg-primary-foreground/20 text-primary-foreground rounded-pill px-5 py-3 text-sm font-medium transition-all duration-200 ease-premium backdrop-blur-sm"
            >
              <Sparkles className="w-4 h-4 opacity-60" />
              <span>{link}</span>
              <ChevronRight className="w-4 h-4 opacity-50 group-hover:translate-x-0.5 transition-transform" />
            </button>
          ))}
        </motion.div>

        <p className="text-primary-foreground/60 text-sm mt-6">
          <strong className="text-primary-foreground/80">Are you a business customer?</strong>{" "}
          Visit our{" "}
          <a href="#" className="underline hover:text-primary-foreground transition-colors">
            Business Support centre
          </a>
        </p>
      </div>
    </section>
  );
};

export default HeroSearch;
