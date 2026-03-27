import {
  User,
  Receipt,
  Wifi,
  ArrowRightLeft,
  CalendarCheck,
  CreditCard,
  Smartphone,
  ScanLine,
} from "lucide-react";
import { motion } from "framer-motion";

const categories = [
  { icon: User, label: "Account", desc: "Manage your profile & settings" },
  { icon: Receipt, label: "Billing", desc: "Payments, charges & invoices" },
  { icon: Wifi, label: "Broadband", desc: "Speed, setup & troubleshooting" },
  { icon: ArrowRightLeft, label: "Joining & Leaving", desc: "Switch, cancel or transfer" },
  { icon: CalendarCheck, label: "Pay Monthly", desc: "Plans, upgrades & extras" },
  { icon: CreditCard, label: "Pay As You Go", desc: "Top-ups, bundles & balances" },
  { icon: ScanLine, label: "SIM & eSIM", desc: "Activate, replace or transfer" },
  { icon: Smartphone, label: "Phones & Devices", desc: "Setup, repair & compatibility" },
];

const CategoryGrid = () => {
  return (
    <section className="py-16 md:py-24 bg-surface">
      <div className="container">
        <h2 className="text-2xl md:text-3xl font-bold text-foreground text-center mb-12 tracking-tight">
          Explore all help topics
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {categories.map((cat, i) => (
            <motion.button
              key={cat.label}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
              className="group relative bg-background rounded-lg p-6 text-left shadow-card hover:shadow-card-hover hover:-translate-y-1 transition-all duration-300 ease-premium overflow-hidden"
            >
              {/* Bottom red line on hover */}
              <div className="absolute bottom-0 left-0 w-0 h-[3px] bg-primary group-hover:w-full transition-all duration-300 ease-premium" />

              <cat.icon className="w-7 h-7 text-primary mb-4 stroke-[1.8]" />
              <h3 className="text-base font-semibold text-foreground mb-1">{cat.label}</h3>
              <p className="text-sm text-muted-foreground">{cat.desc}</p>

              <span className="mt-4 inline-flex items-center text-sm font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                See all
                <svg className="w-4 h-4 ml-1 group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </span>
            </motion.button>
          ))}
        </div>
      </div>
    </section>
  );
};

export default CategoryGrid;
