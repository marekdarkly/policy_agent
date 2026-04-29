import { ArrowUpRight } from "lucide-react";
import { motion } from "framer-motion";

const questions = [
  { q: "What are IBANs and SWIFT codes?", category: "International", time: "1 min read" },
  { q: "I have a problem with a payment that's come out of my account", category: "Payments", time: "2 min read" },
  { q: "Find the address and opening hours of one of our locations", category: "Branches", time: "30s" },
  { q: "How do I find my sort code and account number?", category: "Accounts", time: "1 min read" },
  { q: "How do I follow up with you about my complaint?", category: "Customer service", time: "2 min read" },
  { q: "How do I reset my Online Banking password?", category: "Online Banking", time: "1 min read" },
  { q: "How do I report a lost or stolen card?", category: "Cards", time: "30s" },
  { q: "What are your telephone banking hours?", category: "Contact", time: "30s" },
];

interface BarclaysPopularQuestionsProps {
  onQuestionClick?: (question: string) => void;
}

const BarclaysPopularQuestions = ({ onQuestionClick }: BarclaysPopularQuestionsProps) => {
  return (
    <section className="py-20 md:py-28 bg-background">
      <div className="container">
        <div className="max-w-3xl mx-auto mb-12">
          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground/80 font-medium mb-3">
            Popular questions
          </p>
          <h2 className="font-display text-4xl md:text-5xl text-foreground leading-[1.05] mb-4">
            What people ask us most.
          </h2>
          <p className="text-base text-muted-foreground max-w-xl">
            Searched, ranked, and answered by our specialist team — refreshed weekly from
            real customer conversations.
          </p>
        </div>

        <div className="max-w-3xl mx-auto rounded-2xl bg-card ring-hairline overflow-hidden">
          <ol className="divide-y divide-border">
            {questions.map((item, i) => (
              <motion.li
                key={item.q}
                initial={{ opacity: 0, y: 8 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.04, duration: 0.3, ease: [0.2, 0.8, 0.2, 1] }}
              >
                <button
                  onClick={() => onQuestionClick?.(item.q)}
                  className="group w-full flex items-center gap-5 px-5 md:px-7 py-5 text-left hover:bg-foreground/[0.02] transition-colors"
                >
                  <span className="text-[11px] font-mono tabular-nums text-muted-foreground/70 w-7 shrink-0">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-[15px] md:text-base text-foreground font-medium leading-snug group-hover:text-foreground">
                      {item.q}
                    </div>
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                      <span className="inline-flex items-center gap-1.5">
                        <span className="w-1 h-1 rounded-full bg-accent" />
                        {item.category}
                      </span>
                      <span>·</span>
                      <span>{item.time}</span>
                    </div>
                  </div>
                  <div className="w-9 h-9 rounded-full bg-foreground/[0.03] group-hover:bg-ink group-hover:text-cream flex items-center justify-center transition-all shrink-0">
                    <ArrowUpRight className="w-4 h-4 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 transition-transform" />
                  </div>
                </button>
              </motion.li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
};

export default BarclaysPopularQuestions;
