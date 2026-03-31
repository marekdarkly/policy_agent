import { Monitor, CreditCard, Wallet, Smartphone, Home, ShieldCheck, PiggyBank, Globe, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";

const topics = [
  {
    icon: Monitor,
    title: "Online Banking",
    desc: "Manage your account, view statements, and make transfers online.",
    links: [
      "How can I find my membership number?",
      "How can I log in without my PINsentry card reader?",
      "How do I transfer money between my accounts?",
      "I've forgotten my Online Banking passcode",
      "How do I set up a new payee?",
    ],
    allLink: "All Online Banking help",
  },
  {
    icon: Wallet,
    title: "Payments",
    desc: "Sending money, Direct Debits, standing orders and international transfers.",
    links: [
      "How do I make a payment to someone new?",
      "How do I send money abroad?",
      "What's the difference between Faster Payments, CHAPS and BACS?",
      "How do I cancel a Direct Debit?",
      "What are the cut-off times for payments?",
    ],
    allLink: "All payments help",
  },
  {
    icon: CreditCard,
    title: "Debit cards",
    desc: "PIN reminders, contactless limits, lost or stolen cards.",
    links: [
      "My card doesn't work. What should I do?",
      "How do I get a reminder of my debit card PIN?",
      "What is the contactless payment limit?",
      "How do I report a lost or stolen card?",
    ],
    allLink: "All card help",
  },
  {
    icon: Smartphone,
    title: "The app",
    desc: "Download, register, and get the most out of mobile banking.",
    links: [
      "How do I register for the app?",
      "What happens if I get a new phone?",
      "How is Mobile PINsentry different from the card reader?",
      "Can I use fingerprint or face login?",
      "How do I deposit a cheque using the app?",
    ],
    allLink: "All app help",
  },
  {
    icon: Home,
    title: "Mortgages",
    desc: "Applications, repayments, rates and switching your mortgage.",
    links: [
      "How do I find out my mortgage balance and interest rate?",
      "When does my fixed rate end?",
      "How do I make an overpayment?",
      "Can I switch to a new mortgage deal?",
    ],
    allLink: "All mortgages help",
  },
  {
    icon: ShieldCheck,
    title: "Fraud & security",
    desc: "Stay safe online and report suspicious activity.",
    links: [
      "Will I ever have to give my PIN online or over the phone?",
      "I think I've been a victim of fraud",
      "How do I report a suspicious email or text?",
      "What is Strong Customer Authentication?",
    ],
    allLink: "All fraud help",
  },
  {
    icon: PiggyBank,
    title: "Savings & ISAs",
    desc: "Interest rates, ISA allowances, and managing your savings.",
    links: [
      "What savings accounts do you offer?",
      "How do I open a new ISA?",
      "What is the current ISA allowance?",
      "How do I transfer an ISA from another provider?",
    ],
    allLink: "All savings help",
  },
  {
    icon: Globe,
    title: "International",
    desc: "Travelling abroad, foreign payments, and exchange rates.",
    links: [
      "What are IBANs and SWIFT codes?",
      "Do I need to tell you before I travel?",
      "What are the fees for using my card abroad?",
      "How do I send money to another country?",
    ],
    allLink: "All international help",
  },
];

const BarclaysTopics = () => {
  return (
    <section className="py-16 md:py-24 bg-surface">
      <div className="container">
        <h2 className="text-2xl md:text-3xl font-bold text-foreground text-center mb-3 tracking-tight">
          Popular Topics
        </h2>
        <p className="text-muted-foreground text-center mb-12 max-w-lg mx-auto">
          Browse our most popular help categories to find the answers you need.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {topics.map((topic, i) => (
            <motion.div
              key={topic.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
              className="group bg-background rounded-lg shadow-card hover:shadow-card-hover transition-all duration-300 ease-premium overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="px-5 pt-5 pb-3">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-9 h-9 rounded-lg bg-[hsl(var(--barclays-primary))]/10 flex items-center justify-center shrink-0">
                    <topic.icon className="w-4.5 h-4.5 text-[hsl(var(--barclays-primary))]" />
                  </div>
                  <h3 className="text-base font-bold text-foreground">{topic.title}</h3>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">{topic.desc}</p>
              </div>

              {/* Links */}
              <ul className="px-5 pb-4 space-y-1.5 flex-1">
                {topic.links.map((link) => (
                  <li key={link}>
                    <button className="text-sm text-[hsl(var(--barclays-primary))] hover:underline text-left leading-snug flex items-start gap-1.5">
                      <ChevronRight className="w-3.5 h-3.5 mt-0.5 shrink-0 opacity-40" />
                      <span>{link}</span>
                    </button>
                  </li>
                ))}
              </ul>

              {/* All link */}
              <div className="border-t border-border px-5 py-3">
                <button className="text-sm font-semibold text-[hsl(var(--barclays-primary))] hover:underline inline-flex items-center gap-1 group-hover:gap-1.5 transition-all">
                  {topic.allLink}
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default BarclaysTopics;
