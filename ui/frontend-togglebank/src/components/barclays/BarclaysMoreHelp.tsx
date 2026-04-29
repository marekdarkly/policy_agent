import { ArrowUpRight } from "lucide-react";
import { motion } from "framer-motion";

const helpSections = [
  {
    title: "About you",
    links: [
      { name: "Text alerts", sub: "Set up balance and transaction alerts" },
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
    <section className="relative py-20 md:py-28 bg-secondary/40">
      <div className="absolute inset-x-0 top-0 section-divider" />
      <div className="container relative">
        <div className="max-w-3xl mb-14">
          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground/80 font-medium mb-3">
            Help directory
          </p>
          <h2 className="font-display text-4xl md:text-5xl text-foreground leading-[1.05] mb-4">
            The full library, neatly indexed.
          </h2>
          <p className="text-base text-muted-foreground max-w-xl">
            Every guide, FAQ, and policy — organised so you can jump straight to what you
            need.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {helpSections.map((section, i) => (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
              className="bg-card rounded-2xl p-7 ring-hairline"
            >
              <div className="flex items-center justify-between mb-5 pb-4 border-b border-border">
                <h3 className="text-base font-semibold text-foreground tracking-tight">
                  {section.title}
                </h3>
                <span className="text-xs font-mono tabular-nums text-muted-foreground/60">
                  {String(section.links.length).padStart(2, "0")}
                </span>
              </div>
              <ul className="space-y-4">
                {section.links.map((link) => (
                  <li key={link.name}>
                    <button className="group text-left w-full">
                      <span className="text-sm font-medium text-foreground group-hover:text-accent transition-colors flex items-center gap-1">
                        {link.name}
                        <ArrowUpRight className="w-3 h-3 opacity-0 -translate-x-0.5 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                      </span>
                      <span className="text-xs text-muted-foreground block mt-0.5">
                        {link.sub}
                      </span>
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
