import { CheckCircle2, ArrowUpRight, Wifi, CreditCard, Smartphone, Globe, Activity } from "lucide-react";
import { motion } from "framer-motion";

const services = [
  { icon: Globe, name: "Online Banking", uptime: "99.998%" },
  { icon: Smartphone, name: "Mobile App", uptime: "99.997%" },
  { icon: CreditCard, name: "Card Payments", uptime: "100.000%" },
  { icon: Wifi, name: "Open Banking", uptime: "99.996%" },
];

const BarclaysServiceStatus = () => {
  return (
    <section className="py-16 md:py-20 bg-background">
      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
          className="max-w-5xl mx-auto bg-card rounded-3xl ring-hairline overflow-hidden"
        >
          <div className="px-7 md:px-10 py-7 md:py-8 flex flex-col md:flex-row md:items-center md:justify-between gap-6 border-b border-border">
            <div>
              <div className="inline-flex items-center gap-2 mb-3">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald2 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald2"></span>
                </span>
                <span className="text-[11px] uppercase tracking-[0.18em] font-semibold text-emerald2">
                  All systems normal
                </span>
              </div>
              <h3 className="text-xl md:text-2xl font-display text-foreground">
                Service status — live.
              </h3>
              <p className="text-sm text-muted-foreground mt-1.5">
                Updated 2 minutes ago · 90-day uptime average <span className="font-mono text-foreground">99.997%</span>
              </p>
            </div>
            <button className="inline-flex items-center gap-2 bg-foreground/[0.04] hover:bg-foreground/[0.08] text-foreground font-semibold text-sm px-5 py-2.5 rounded-xl transition-colors shrink-0">
              <Activity className="w-4 h-4" />
              Full status page
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-y md:divide-y-0 divide-border">
            {services.map((service, i) => (
              <motion.div
                key={service.name}
                initial={{ opacity: 0, y: 8 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.05 + i * 0.05, duration: 0.3, ease: [0.2, 0.8, 0.2, 1] }}
                className="px-6 py-5 flex flex-col gap-3"
              >
                <div className="flex items-center gap-2.5">
                  <service.icon className="w-4 h-4 text-muted-foreground" strokeWidth={1.75} />
                  <p className="text-sm font-medium text-foreground">{service.name}</p>
                </div>
                <div className="flex items-end justify-between">
                  <span className="text-xs text-emerald2 inline-flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Operational
                  </span>
                  <span className="text-[11px] font-mono tabular-nums text-muted-foreground">
                    {service.uptime}
                  </span>
                </div>
                {/* Tiny uptime bars */}
                <div className="flex gap-px h-3">
                  {Array.from({ length: 30 }).map((_, j) => (
                    <span
                      key={j}
                      className="flex-1 rounded-sm bg-emerald2/70"
                      style={{ opacity: 0.4 + (j / 30) * 0.6 }}
                    />
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default BarclaysServiceStatus;
