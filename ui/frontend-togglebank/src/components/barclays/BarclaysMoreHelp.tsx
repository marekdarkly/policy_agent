import { ChevronRight } from "lucide-react";
import { motion } from "framer-motion";

const helpSections = [
  {
    title: "About you",
    links: [
      { name: "Text Alerts", sub: "Set up balance and transaction alerts" },
      { name: "Your details", sub: "Update name, address, or phone number" },
      { name: "Lost or stolen card", sub: "Report and order a replacement" },
      { name: "Security and fraud", sub: "Protect your account" },
      { name: "Travel abroad", sub: "Using your card overseas" },
      { name: "Your credit rating", sub: "Check and improve your score" },
    ],
  },
  {
    title: "Bank accounts",
    links: [
      { name: "Current accounts", sub: "Everyday banking and features" },
      { name: "Opening an account", sub: "What you'll need to get started" },
      { name: "Switching", sub: "Move your account in 7 working days" },
      { name: "Statements and balances", sub: "View, download, or request" },
      { name: "Students and graduates", sub: "Accounts designed for you" },
      { name: "International accounts", sub: "Banking from overseas" },
    ],
  },
  {
    title: "Products",
    links: [
      { name: "Debit cards", sub: "PIN, contactless, and card controls" },
      { name: "Credit cards", sub: "Balances, payments, and limits" },
      { name: "Savings and ISAs", sub: "Rates, allowances, and accounts" },
      { name: "Loans and overdrafts", sub: "Borrowing and repayments" },
      { name: "Mortgages", sub: "Applications, rates, and switching" },
      { name: "Insurance", sub: "Travel, home, and life cover" },
    ],
  },
  {
    title: "Ways to bank",
    links: [
      { name: "Online Banking", sub: "Log in, registration, and features" },
      { name: "Mobile banking", sub: "App setup and troubleshooting" },
      { name: "Telephone Banking", sub: "Phone numbers and opening hours" },
      { name: "In branch", sub: "Find locations and book appointments" },
      { name: "Make a payment", sub: "Transfers, BACS, and CHAPS" },
      { name: "Direct Debits", sub: "Set up, manage, or cancel" },
    ],
  },
];

const BarclaysMoreHelp = () => {
  return (
    <section className="py-16 md:py-24 bg-surface">
      <div className="container">
        <h2 className="text-2xl md:text-3xl font-bold text-foreground text-center mb-3 tracking-tight">
          Find more help here
        </h2>
        <p className="text-muted-foreground text-center mb-12 max-w-lg mx-auto">
          Browse all of our help categories to find exactly what you need.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {helpSections.map((section, i) => (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
              className="bg-background rounded-xl p-6 shadow-card"
            >
              <h3 className="text-base font-bold text-foreground mb-5 pb-3 border-b-2 border-[hsl(var(--barclays-primary))]">
                {section.title}
              </h3>
              <ul className="space-y-3.5">
                {section.links.map((link) => (
                  <li key={link.name}>
                    <button className="group text-left w-full">
                      <span className="text-sm font-medium text-[hsl(var(--barclays-primary))] group-hover:underline flex items-center gap-1">
                        {link.name}
                        <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </span>
                      <span className="text-xs text-muted-foreground block mt-0.5">{link.sub}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default BarclaysMoreHelp;
