import { ShieldAlert, MapPin, CreditCard, Smartphone, ArrowRightLeft, HelpCircle } from "lucide-react";
import { motion } from "framer-motion";

const actions = [
  { icon: ShieldAlert, label: "Report fraud", color: "text-rose-600 bg-rose-50" },
  { icon: MapPin, label: "Find a branch", color: "text-[hsl(var(--barclays-primary))] bg-[hsl(var(--barclays-primary))]/5" },
  { icon: CreditCard, label: "Lost card", color: "text-amber-600 bg-amber-50" },
  { icon: Smartphone, label: "Get the app", color: "text-[hsl(var(--barclays-primary))] bg-[hsl(var(--barclays-primary))]/5" },
  { icon: ArrowRightLeft, label: "Make a transfer", color: "text-emerald-600 bg-emerald-50" },
  { icon: HelpCircle, label: "Contact us", color: "text-[hsl(var(--barclays-primary))] bg-[hsl(var(--barclays-primary))]/5" },
];

const BarclaysQuickActions = () => {
  return (
    <section className="py-8 bg-background border-b border-border">
      <div className="container">
        <div className="flex items-center gap-3 overflow-x-auto pb-1 scrollbar-none justify-center flex-wrap">
          {actions.map((action, i) => (
            <motion.button
              key={action.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 + i * 0.05, duration: 0.3, ease: [0.2, 0.8, 0.2, 1] }}
              className="flex flex-col items-center gap-2 px-5 py-3 rounded-xl hover:bg-surface transition-colors duration-200 group shrink-0"
            >
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${action.color} group-hover:scale-105 transition-transform duration-200`}>
                <action.icon className="w-5.5 h-5.5" />
              </div>
              <span className="text-xs font-medium text-foreground whitespace-nowrap">{action.label}</span>
            </motion.button>
          ))}
        </div>
      </div>
    </section>
  );
};

export default BarclaysQuickActions;
