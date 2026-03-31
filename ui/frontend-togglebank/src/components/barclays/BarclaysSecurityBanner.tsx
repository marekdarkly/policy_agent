import { ShieldCheck, AlertTriangle, Lock, Eye } from "lucide-react";
import { motion } from "framer-motion";

const tips = [
  {
    icon: AlertTriangle,
    title: "Scam warnings",
    desc: "We'll never ask for your full PIN or password by email, text, or phone.",
  },
  {
    icon: Lock,
    title: "Strong authentication",
    desc: "Use PINsentry or the app to verify it's you when logging in or making payments.",
  },
  {
    icon: Eye,
    title: "Check your statements",
    desc: "Regularly review transactions and report anything you don't recognise immediately.",
  },
];

const BarclaysSecurityBanner = () => {
  return (
    <section className="py-16 md:py-20 bg-[hsl(var(--barclays-dark))]">
      <div className="container">
        <div className="text-center mb-12">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
            className="inline-flex items-center gap-2 bg-white/10 rounded-full px-4 py-1.5 mb-4"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-semibold text-white/90 tracking-wide uppercase">Security centre</span>
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.05, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
            className="text-2xl md:text-3xl font-bold text-white tracking-tight mb-3"
          >
            Keeping your money safe
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
            className="text-white/60 max-w-md mx-auto"
          >
            Your security is our priority. Here's how to protect yourself.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {tips.map((tip, i) => (
            <motion.div
              key={tip.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 + i * 0.08, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
              className="bg-white/[0.06] backdrop-blur-sm rounded-xl p-6 border border-white/10 hover:bg-white/[0.1] transition-colors duration-300"
            >
              <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center mb-4">
                <tip.icon className="w-5 h-5 text-emerald-400" />
              </div>
              <h3 className="text-base font-bold text-white mb-2">{tip.title}</h3>
              <p className="text-sm text-white/60 leading-relaxed">{tip.desc}</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
          className="text-center mt-10"
        >
          <button className="inline-flex items-center gap-2 bg-white text-[hsl(var(--barclays-dark))] font-semibold text-sm px-6 py-2.5 rounded-md hover:bg-white/90 transition-colors">
            <ShieldCheck className="w-4 h-4" />
            Visit our Security Centre
          </button>
        </motion.div>
      </div>
    </section>
  );
};

export default BarclaysSecurityBanner;
