import { ChevronRight } from "lucide-react";
import { motion } from "framer-motion";

const faqs = [
  "I need help understanding my bill",
  "I can't log in to my account",
  "How do I activate and set up my new SIM?",
  "How do I pay my bill?",
  "How do I cancel my mobile or broadband contract?",
];

const FAQSection = () => {
  return (
    <section className="py-16 md:py-24 bg-background">
      <div className="container">
        <h2 className="text-2xl md:text-3xl font-bold text-foreground text-center mb-12 tracking-tight">
          Most frequently asked questions
        </h2>

        <div className="max-w-3xl mx-auto space-y-3">
          {faqs.map((faq, i) => (
            <motion.button
              key={faq}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
              className="group w-full flex items-center justify-between p-5 bg-background border border-border rounded-lg hover:shadow-card hover:border-primary/20 transition-all duration-300 ease-premium text-left"
            >
              <span className="text-base font-medium text-foreground group-hover:text-primary transition-colors">
                {faq}
              </span>
              <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all shrink-0 ml-4" />
            </motion.button>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FAQSection;
