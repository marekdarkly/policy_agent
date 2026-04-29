import { ShieldAlert, MapPin, CreditCard, Smartphone, ArrowRightLeft, HelpCircle, ArrowUpRight } from "lucide-react";
import { motion } from "framer-motion";

const actions = [
  { icon: ShieldAlert, label: "Report fraud", desc: "Lock & dispute" },
  { icon: CreditCard, label: "Lost or stolen card", desc: "Freeze instantly" },
  { icon: ArrowRightLeft, label: "Make a transfer", desc: "Domestic & wires" },
  { icon: Smartphone, label: "Get the app", desc: "iOS · Android" },
  { icon: MapPin, label: "Find a branch", desc: "12k locations" },
  { icon: HelpCircle, label: "Talk to a banker", desc: "24 / 7 support" },
];

const BarclaysQuickActions = () => {
  return (
    <section className="relative pt-4 pb-14 md:pt-6 md:pb-16 bg-background">
      <div className="container">
        <div className="flex items-end justify-between mb-6">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground/80 font-medium mb-2">
              Most used
            </p>
            <h2 className="text-2xl md:text-3xl font-display text-foreground">
              Skip the small talk.
            </h2>
          </div>
          <a
            href="#"
            className="hidden sm:inline-flex items-center gap-1 text-sm font-medium text-foreground/70 hover:text-foreground"
          >
            All quick actions
            <ArrowUpRight className="w-3.5 h-3.5" />
          </a>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {actions.map((action, i) => (
            <motion.button
              key={action.label}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.05 + i * 0.04, duration: 0.35, ease: [0.2, 0.8, 0.2, 1] }}
              className="group relative bg-card rounded-2xl p-5 text-left ring-hairline hover:shadow-card transition-all duration-300 ease-premium overflow-hidden"
            >
              <div className="relative z-10">
                <div className="w-10 h-10 rounded-xl bg-foreground/[0.04] flex items-center justify-center mb-4 group-hover:bg-accent/10 transition-colors">
                  <action.icon
                    className="w-[18px] h-[18px] text-foreground group-hover:text-accent transition-colors"
                    strokeWidth={1.75}
                  />
                </div>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="text-sm font-semibold text-foreground leading-tight">
                      {action.label}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">{action.desc}</div>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-foreground group-hover:-translate-y-0.5 group-hover:translate-x-0.5 transition-all shrink-0" />
                </div>
              </div>
              <div className="pointer-events-none absolute -inset-px rounded-2xl bg-gradient-to-br from-accent/0 to-accent/0 group-hover:from-accent/[0.04] group-hover:to-transparent transition-colors" />
            </motion.button>
          ))}
        </div>
      </div>
    </section>
  );
};

export default BarclaysQuickActions;
