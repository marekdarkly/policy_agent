import { MessageCircle, Phone, MapPin, ArrowUpRight, Twitter, Linkedin, Github } from "lucide-react";

interface BarclaysFooterProps {
  onChatOpen?: () => void;
}

const BarclaysFooter = ({ onChatOpen }: BarclaysFooterProps) => {
  return (
    <>
      {/* Contact CTA --------------------------------------------------- */}
      <section className="relative py-20 md:py-28 bg-background overflow-hidden">
        <div
          className="absolute inset-0 opacity-60"
          style={{
            background:
              "radial-gradient(700px circle at 50% 0%, hsl(var(--brand-accent) / .12), transparent 55%)",
          }}
        />
        <div className="container relative text-center">
          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground/80 font-medium mb-4">
            Still need a human?
          </p>
          <h2 className="font-display text-4xl md:text-6xl text-foreground leading-[1.02] mb-6 max-w-3xl mx-auto">
            We're here. <em className="not-italic gradient-text">Always.</em>
          </h2>
          <p className="text-base text-muted-foreground mb-10 max-w-md mx-auto">
            Real bankers, no scripts. Pick the way that works best for you.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center max-w-2xl mx-auto">
            <button
              onClick={onChatOpen}
              className="flex-1 inline-flex items-center justify-center gap-2 bg-ink text-cream font-semibold px-7 py-4 rounded-xl hover:bg-ink-2 transition-colors duration-200 shadow-card"
            >
              <MessageCircle className="w-[18px] h-[18px]" />
              Chat with us
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
            <button className="flex-1 inline-flex items-center justify-center gap-2 bg-card text-foreground border border-border font-semibold px-7 py-4 rounded-xl hover:bg-foreground/[0.02] transition-colors duration-200">
              <Phone className="w-[18px] h-[18px]" />
              Call us
            </button>
            <button className="flex-1 inline-flex items-center justify-center gap-2 bg-card text-foreground border border-border font-semibold px-7 py-4 rounded-xl hover:bg-foreground/[0.02] transition-colors duration-200">
              <MapPin className="w-[18px] h-[18px]" />
              Find a branch
            </button>
          </div>
        </div>
      </section>

      {/* Footer -------------------------------------------------------- */}
      <footer className="bg-ink text-cream relative overflow-hidden">
        <div
          className="absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage:
              "linear-gradient(hsl(var(--brand-cream)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--brand-cream)) 1px, transparent 1px)",
            backgroundSize: "72px 72px",
          }}
        />

        <div className="container relative pt-16 pb-10">
          {/* Big brand strip */}
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-8 pb-12 border-b border-cream/10">
            <div>
              <div className="flex items-center gap-3 mb-5">
                <div className="w-10 h-10 rounded-[10px] bg-cream flex items-center justify-center">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="text-ink">
                    <path d="M4 12 L10 6 L20 16 L14 22 Z" fill="currentColor" />
                    <path d="M14 2 L20 8 L17 11 L11 5 Z" fill="currentColor" opacity="0.6"/>
                  </svg>
                </div>
                <div className="leading-none">
                  <div className="font-display text-2xl text-cream">ToggleBank</div>
                  <div className="text-[10px] uppercase tracking-[0.2em] text-cream/50 mt-1">
                    Banking, refined since 1894
                  </div>
                </div>
              </div>
              <p className="text-sm text-cream/55 max-w-md leading-relaxed">
                A modern bank with a 130-year obsession for getting the details right —
                serving 12 million customers across 40 countries.
              </p>
            </div>
            <div className="flex items-center gap-2">
              {[Twitter, Linkedin, Github].map((Icon, i) => (
                <a
                  key={i}
                  href="#"
                  className="w-10 h-10 rounded-xl bg-cream/[0.06] hover:bg-cream/10 border border-cream/10 flex items-center justify-center text-cream/70 hover:text-cream transition-colors"
                  aria-label="social"
                >
                  <Icon className="w-4 h-4" strokeWidth={1.75} />
                </a>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 py-12">
            <div>
              <h4 className="text-[11px] font-semibold text-cream uppercase tracking-[0.18em] mb-5">
                Personal Banking
              </h4>
              <ul className="space-y-3 text-sm text-cream/55">
                <li><a href="#" className="hover:text-cream transition-colors">Current accounts</a></li>
                <li><a href="#" className="hover:text-cream transition-colors">Savings</a></li>
                <li><a href="#" className="hover:text-cream transition-colors">Mortgages</a></li>
                <li><a href="#" className="hover:text-cream transition-colors">Credit cards</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-[11px] font-semibold text-cream uppercase tracking-[0.18em] mb-5">
                Ways to bank
              </h4>
              <ul className="space-y-3 text-sm text-cream/55">
                <li><a href="#" className="hover:text-cream transition-colors">Online Banking</a></li>
                <li><a href="#" className="hover:text-cream transition-colors">Mobile banking</a></li>
                <li><a href="#" className="hover:text-cream transition-colors">Telephone banking</a></li>
                <li><a href="#" className="hover:text-cream transition-colors">Find a branch</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-[11px] font-semibold text-cream uppercase tracking-[0.18em] mb-5">
                Help
              </h4>
              <ul className="space-y-3 text-sm text-cream/55">
                <li><a href="#" className="hover:text-cream transition-colors">Help and support</a></li>
                <li><a href="#" className="hover:text-cream transition-colors">Contact us</a></li>
                <li><a href="#" className="hover:text-cream transition-colors">Accessibility</a></li>
                <li><a href="#" className="hover:text-cream transition-colors">Complaints</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-[11px] font-semibold text-cream uppercase tracking-[0.18em] mb-5">
                About ToggleBank
              </h4>
              <ul className="space-y-3 text-sm text-cream/55">
                <li><a href="#" className="hover:text-cream transition-colors">About us</a></li>
                <li><a href="#" className="hover:text-cream transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-cream transition-colors">Sustainability</a></li>
                <li><a href="#" className="hover:text-cream transition-colors">Investor relations</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-cream/10 pt-7 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-[11px] text-cream/40">
              <span>© 2026 ToggleBank Ltd.</span>
              <span className="hidden md:inline">·</span>
              <span>Authorised by the PRA · Regulated by the FCA & PRA</span>
              <span className="hidden md:inline">·</span>
              <span>Member FDIC · Equal Housing Lender</span>
            </div>
            <div className="flex gap-5 text-[11px] text-cream/40">
              <a href="#" className="hover:text-cream/80 transition-colors">Privacy</a>
              <a href="#" className="hover:text-cream/80 transition-colors">Cookies</a>
              <a href="#" className="hover:text-cream/80 transition-colors">Terms</a>
              <a href="#" className="hover:text-cream/80 transition-colors">Modern Slavery Act</a>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
};

export default BarclaysFooter;
