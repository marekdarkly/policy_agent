import { CheckCircle2, ExternalLink, Wifi, CreditCard, Smartphone, Globe } from "lucide-react";
import { motion } from "framer-motion";

const services = [
  { icon: Globe, name: "Online Banking", status: "Operational" },
  { icon: Smartphone, name: "Mobile App", status: "Operational" },
  { icon: CreditCard, name: "Card Payments", status: "Operational" },
  { icon: Wifi, name: "Open Banking", status: "Operational" },
];

const BarclaysServiceStatus = () => {
  return (
    <section className="py-14 md:py-16 bg-background">
      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
          className="max-w-4xl mx-auto bg-surface rounded-2xl p-8 md:p-10 shadow-card"
        >
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 mb-8">
            <div>
              <div className="flex items-center gap-2.5 mb-2">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                <h3 className="text-lg font-bold text-foreground">All systems operational</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                All ToggleBank services are running normally. Last checked 2 minutes ago.
              </p>
            </div>
            <button className="inline-flex items-center gap-2 bg-[hsl(var(--barclays-primary))] text-white font-semibold text-sm px-5 py-2.5 rounded-md hover:bg-[hsl(var(--barclays-dark))] transition-colors shrink-0">
              Full status page
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {services.map((service, i) => (
              <motion.div
                key={service.name}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 + i * 0.05, duration: 0.3, ease: [0.2, 0.8, 0.2, 1] }}
                className="flex items-center gap-3 bg-background rounded-lg px-4 py-3 border border-border"
              >
                <service.icon className="w-4.5 h-4.5 text-muted-foreground shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{service.name}</p>
                  <div className="flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                    <span className="text-xs text-emerald-600">{service.status}</span>
                  </div>
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
