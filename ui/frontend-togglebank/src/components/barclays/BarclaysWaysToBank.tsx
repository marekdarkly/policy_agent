import { Monitor, Smartphone, Phone, MapPin, ArrowUpRight } from "lucide-react";
import { motion } from "framer-motion";

const ways = [
  {
    icon: Monitor,
    title: "Online Banking",
    desc: "Manage your money 24/7 from any browser. View balances, schedule payments, and reconcile your finances with full-fidelity statements.",
    cta: "Log in to Online Banking",
    meta: "Web · Desktop",
  },
  {
    icon: Smartphone,
    title: "ToggleBank App",
    desc: "Bank on the go with our award-winning app. Deposit cheques, freeze cards, and send instant payments with biometric authentication.",
    cta: "Download the app",
    meta: "iOS · Android",
  },
  {
    icon: Phone,
    title: "Telephone Banking",
    desc: "Speak to a UK-based banker for help with anything — from a stuck Direct Debit to a six-figure transfer. Available 7 days a week.",
    cta: "View phone numbers",
    meta: "7am – 11pm",
  },
  {
    icon: MapPin,
    title: "Visit a branch",
    desc: "Drop into your local branch for face-to-face advice, mortgage consultations, or to open a new account. 12,000 locations worldwide.",
    cta: "Find your nearest branch",
    meta: "12,000+ locations",
  },
];

const BarclaysWaysToBank = () => {
  return (
    <section className="relative py-20 md:py-28 bg-background">
      <div className="container">
        <div className="max-w-3xl mb-14">
          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground/80 font-medium mb-3">
            Ways to bank
          </p>
          <h2 className="font-display text-4xl md:text-5xl text-foreground leading-[1.05] mb-4">
            Wherever you are. However you bank.
          </h2>
          <p className="text-base text-muted-foreground max-w-xl">
            Choose the channel that fits the moment — every interaction is private,
            encrypted, and unified across your account.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {ways.map((way, i) => (
            <motion.div
              key={way.title}
              initial={{ opacity: 0, y: 22 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08, duration: 0.45, ease: [0.2, 0.8, 0.2, 1] }}
              className="group relative bg-ink text-cream rounded-2xl overflow-hidden flex flex-col shadow-card hover-lift"
            >
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                style={{
                  background: "radial-gradient(600px circle at 0% 0%, hsl(var(--brand-accent) / .25), transparent 50%)",
                }}
              />
              <div className="relative p-6 flex flex-col flex-1">
                <div className="flex items-start justify-between mb-5">
                  <div className="w-11 h-11 rounded-xl bg-cream/10 flex items-center justify-center">
                    <way.icon className="w-5 h-5 text-cream" strokeWidth={1.75} />
                  </div>
                  <span className="text-[10px] uppercase tracking-[0.18em] text-cream/50 font-medium">
                    {way.meta}
                  </span>
                </div>

                <h3 className="text-lg font-semibold text-cream mb-2 tracking-tight">
                  {way.title}
                </h3>
                <p className="text-sm text-cream/65 leading-relaxed flex-1">{way.desc}</p>

                <button className="mt-6 inline-flex items-center gap-1.5 text-sm font-semibold text-cream group-hover:gap-2 transition-all">
                  {way.cta}
                  <ArrowUpRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default BarclaysWaysToBank;
