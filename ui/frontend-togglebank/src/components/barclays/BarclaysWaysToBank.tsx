import { Monitor, Smartphone, Phone, MapPin, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";

const ways = [
  {
    icon: Monitor,
    title: "Online Banking",
    desc: "Manage your money 24/7. View balances, make payments, and manage Direct Debits from your computer.",
    cta: "Log in to Online Banking",
    accent: "from-[hsl(var(--barclays-primary))] to-[hsl(var(--barclays-dark))]",
  },
  {
    icon: Smartphone,
    title: "ToggleBank App",
    desc: "Bank on the go with our award-winning app. Deposit cheques, freeze cards, and send money instantly.",
    cta: "Download the app",
    accent: "from-[hsl(var(--barclays-primary))] to-[hsl(var(--barclays-sky))]",
  },
  {
    icon: Phone,
    title: "Telephone Banking",
    desc: "Speak to our team for help with your account. Available 7 days a week, 7am to 11pm.",
    cta: "View phone numbers",
    accent: "from-[hsl(var(--barclays-dark))] to-[hsl(var(--barclays-primary))]",
  },
  {
    icon: MapPin,
    title: "Visit a branch",
    desc: "Pop into your local branch for face-to-face help. Book an appointment or find opening hours.",
    cta: "Find your nearest branch",
    accent: "from-[hsl(var(--barclays-sky))] to-[hsl(var(--barclays-primary))]",
  },
];

const BarclaysWaysToBank = () => {
  return (
    <section className="py-16 md:py-24 bg-background">
      <div className="container">
        <h2 className="text-2xl md:text-3xl font-bold text-foreground text-center mb-3 tracking-tight">
          Ways to bank with us
        </h2>
        <p className="text-muted-foreground text-center mb-12 max-w-lg mx-auto">
          Choose how you manage your money — at home, on the go, or in person.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {ways.map((way, i) => (
            <motion.div
              key={way.title}
              initial={{ opacity: 0, y: 28 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08, duration: 0.45, ease: [0.2, 0.8, 0.2, 1] }}
              className="group relative bg-background rounded-xl shadow-card hover:shadow-card-hover transition-all duration-300 ease-premium overflow-hidden flex flex-col"
            >
              {/* Gradient top strip */}
              <div className={`h-1.5 bg-gradient-to-r ${way.accent}`} />

              <div className="p-6 flex flex-col flex-1">
                <div className="w-12 h-12 rounded-xl bg-[hsl(var(--barclays-primary))]/8 flex items-center justify-center mb-4">
                  <way.icon className="w-6 h-6 text-[hsl(var(--barclays-primary))]" />
                </div>

                <h3 className="text-lg font-bold text-foreground mb-2">{way.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed flex-1">{way.desc}</p>

                <button className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-[hsl(var(--barclays-primary))] group-hover:gap-2 transition-all">
                  {way.cta}
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

export default BarclaysWaysToBank;
