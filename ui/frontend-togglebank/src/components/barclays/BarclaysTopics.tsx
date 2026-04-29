import {
  Monitor,
  CreditCard,
  Wallet,
  Smartphone,
  Home,
  ShieldCheck,
  PiggyBank,
  Globe,
  ArrowUpRight,
} from "lucide-react";
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
    ],
    allLink: "All Online Banking help",
  },
  {
    icon: Wallet,
    title: "Payments",
    desc: "Sending money, Direct Debits, standing orders, and international wires.",
    links: [
      "How do I make a payment to someone new?",
      "How do I send money abroad?",
      "What's the difference between Faster Payments, CHAPS and BACS?",
      "How do I cancel a Direct Debit?",
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
      "Can I use fingerprint or face login?",
      "How do I deposit a cheque using the app?",
    ],
    allLink: "All app help",
  },
  {
    icon: Home,
    title: "Mortgages",
    desc: "Applications, repayments, rates, and switching your mortgage.",
    links: [
      "How do I find out my mortgage balance?",
      "When does my fixed rate end?",
      "How do I make an overpayment?",
      "Can I switch to a new mortgage deal?",
    ],
    allLink: "All mortgages help",
  },
  {
    icon: ShieldCheck,
    title: "Fraud & security",
    desc: "Stay safe online, recognise scams, and report suspicious activity.",
    links: [
      "Will I ever have to give my PIN over the phone?",
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
    <section className="relative py-20 md:py-28 bg-secondary/40">
      <div className="absolute inset-x-0 top-0 section-divider" />
      <div className="container relative">
        <div className="max-w-3xl mb-14">
          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground/80 font-medium mb-3">
            Browse by topic
          </p>
          <h2 className="font-display text-4xl md:text-5xl text-foreground leading-[1.05] mb-4">
            Eight categories. Every answer.
          </h2>
          <p className="text-base text-muted-foreground max-w-xl">
            From day-to-day banking to international wires — explore the help library or
            jump straight into a guide.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {topics.map((topic, i) => (
            <motion.div
              key={topic.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
              className="group relative bg-card rounded-2xl ring-hairline overflow-hidden flex flex-col hover-lift"
            >
              <div className="px-6 pt-6 pb-4">
                <div className="flex items-start justify-between mb-5">
                  <div className="w-11 h-11 rounded-xl bg-foreground/[0.04] flex items-center justify-center group-hover:bg-ink group-hover:text-cream transition-colors">
                    <topic.icon className="w-5 h-5" strokeWidth={1.75} />
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-muted-foreground/60 group-hover:text-foreground group-hover:-translate-y-0.5 group-hover:translate-x-0.5 transition-all" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-1.5 tracking-tight">
                  {topic.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{topic.desc}</p>
              </div>

              <ul className="px-6 pb-5 space-y-2 flex-1">
                {topic.links.map((link) => (
                  <li key={link}>
                    <button className="text-sm text-foreground/75 hover:text-accent text-left leading-snug">
                      · {link}
                    </button>
                  </li>
                ))}
              </ul>

              <div className="border-t border-border px-6 py-4">
                <button className="text-sm font-semibold text-foreground inline-flex items-center gap-1 group-hover:gap-2 transition-all">
                  {topic.allLink}
                  <ArrowUpRight className="w-3.5 h-3.5" />
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
