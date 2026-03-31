import { ChevronRight } from "lucide-react";
import { motion } from "framer-motion";

const questions = [
  { q: "What are IBANs and SWIFT codes?", category: "International" },
  { q: "I have a problem with a payment that's come out of my account", category: "Payments" },
  { q: "Find the address and opening hours of one of our locations", category: "Branches" },
  { q: "How do I find my sort code and account number?", category: "Accounts" },
  { q: "How do I follow up with you about my complaint?", category: "Customer service" },
  { q: "How do I reset my Online Banking password?", category: "Online Banking" },
  { q: "How do I report a lost or stolen card?", category: "Cards" },
  { q: "What are your telephone banking hours?", category: "Contact" },
];

interface BarclaysPopularQuestionsProps {
  onQuestionClick?: (question: string) => void;
}

const BarclaysPopularQuestions = ({ onQuestionClick }: BarclaysPopularQuestionsProps) => {
  return (
    <section className="py-16 md:py-20 bg-background">
      <div className="container">
        <h2 className="text-2xl md:text-3xl font-bold text-foreground text-center mb-3 tracking-tight">
          Popular questions
        </h2>
        <p className="text-muted-foreground text-center mb-10 max-w-md mx-auto">
          Quick answers to the things our customers ask about most.
        </p>

        <div className="max-w-3xl mx-auto">
          <ol className="space-y-0 divide-y divide-border">
            {questions.map((item, i) => (
              <motion.li
                key={item.q}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05, duration: 0.35, ease: [0.2, 0.8, 0.2, 1] }}
              >
                <button
                  onClick={() => onQuestionClick?.(item.q)}
                  className="group w-full flex items-center gap-4 py-4 text-left hover:bg-surface/50 transition-colors duration-200 px-3 -mx-3 rounded-md"
                >
                  <span className="text-sm font-bold text-[hsl(var(--barclays-primary))] tabular-nums w-7 shrink-0">
                    {i + 1}.
                  </span>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm md:text-base text-[hsl(var(--barclays-primary))] font-medium group-hover:underline block">
                      {item.q}
                    </span>
                    <span className="text-xs text-muted-foreground mt-0.5 block">{item.category}</span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-[hsl(var(--barclays-primary))] group-hover:translate-x-0.5 transition-all shrink-0" />
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
