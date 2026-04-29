import { ShieldCheck, AlertTriangle, Lock, Eye, ArrowUpRight } from "lucide-react";
import { motion } from "framer-motion";

const tips = [
  {
    icon: AlertTriangle,
    title: "Spot a scam",
    desc: "We will never ask for your full PIN or password by email, text, or phone — no exceptions.",
    label: "Awareness",
  },
  {
    icon: Lock,
    title: "Strong authentication",
    desc: "PINsentry, biometrics, and step-up verification keep every payment secure end-to-end.",
    label: "Protection",
  },
  {
    icon: Eye,
    title: "Always-on monitoring",
    desc: "Real-time anomaly detection on every transaction, with instant alerts to your phone.",
    label: "Surveillance",
  },
];

const BarclaysSecurityBanner = () => {
  return (
    <section className="relative py-20 md:py-28 bg-ink overflow-hidden">
      {/* Ambient glow */}
      <div
        className="absolute inset-0 opacity-70"
        style={{
          background:
            "radial-gradient(800px circle at 20% 0%, hsl(var(--brand-accent) / .25), transparent 50%), radial-gradient(700px circle at 90% 100%, hsl(var(--brand-violet) / .22), transparent 50%)",
        }}
      />
      {/* Grid texture */}
      <div
        className="absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage:
            "linear-gradient(hsl(var(--brand-cream)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--brand-cream)) 1px, transparent 1px)",
          backgroundSize: "56px 56px",
        }}
      />

      <div className="container relative">
        <div className="max-w-3xl mb-14">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
            className="inline-flex items-center gap-2 bg-cream/[0.06] border border-cream/10 rounded-full px-3 py-1.5 mb-5"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald2" />
            <span className="text-[10px] font-semibold text-cream/80 tracking-[0.2em] uppercase">
              Security centre
            </span>
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.05, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
            className="font-display text-4xl md:text-5xl text-cream leading-[1.05] mb-4"
          >
            Your money. Defended at every layer.
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
            className="text-cream/65 max-w-xl text-base"
          >
            Three intersecting systems — vigilance, authentication, and monitoring — quietly
            stand between you and risk, every second of every day.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {tips.map((tip, i) => (
            <motion.div
              key={tip.title}
              initial={{ opacity: 0, y: 22 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 + i * 0.08, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
              className="group relative bg-cream/[0.04] backdrop-blur-sm rounded-2xl p-7 border border-cream/10 hover:bg-cream/[0.06] transition-colors duration-300"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="w-11 h-11 rounded-xl bg-cream/10 flex items-center justify-center">
                  <tip.icon className="w-5 h-5 text-emerald2" strokeWidth={1.75} />
                </div>
                <span className="text-[10px] uppercase tracking-[0.18em] text-cream/40 font-medium">
                  {tip.label}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-cream mb-2 tracking-tight">
                {tip.title}
              </h3>
              <p className="text-sm text-cream/60 leading-relaxed">{tip.desc}</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
          className="mt-12 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5 p-6 rounded-2xl bg-cream/[0.04] border border-cream/10"
        >
          <div>
            <h4 className="text-base font-semibold text-cream mb-1">Need to report something now?</h4>
            <p className="text-sm text-cream/60">
              24/7 fraud line · Instant card freeze · Phishing report
            </p>
          </div>
          <button className="inline-flex items-center gap-2 bg-cream text-ink font-semibold text-sm px-5 py-3 rounded-xl hover:bg-cream/90 transition-colors shrink-0">
            <ShieldCheck className="w-4 h-4" />
            Visit Security Centre
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </motion.div>
      </div>
    </section>
  );
};

export default BarclaysSecurityBanner;
