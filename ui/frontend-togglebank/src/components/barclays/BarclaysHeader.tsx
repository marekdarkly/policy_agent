import { Search, Menu, X, ChevronDown } from "lucide-react";
import { useEffect, useState } from "react";

const NAV = [
  "Personal",
  "Wealth",
  "Business",
  "Mortgages",
  "Investing",
];

const BarclaysHeader = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`sticky top-0 z-50 transition-all duration-300 ${
        scrolled
          ? "glass border-b border-border/80 shadow-sm"
          : "bg-background/40 border-b border-transparent"
      }`}
    >
      <div className="container flex items-center justify-between h-16">
        <div className="flex items-center gap-10">
          <a href="/" className="flex items-center gap-2.5 group">
            <div className="relative">
              <div className="w-9 h-9 rounded-[10px] bg-ink flex items-center justify-center shadow-sm">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="text-cream">
                  <path d="M4 12 L10 6 L20 16 L14 22 Z" fill="currentColor" />
                  <path d="M14 2 L20 8 L17 11 L11 5 Z" fill="currentColor" opacity="0.6"/>
                </svg>
              </div>
              <div className="absolute -inset-px rounded-[10px] bg-gradient-to-tr from-accent/0 via-accent/30 to-accent/0 opacity-0 group-hover:opacity-100 transition-opacity blur-sm" />
            </div>
            <div className="flex flex-col leading-none">
              <span className="font-display text-[22px] tracking-tight text-foreground">
                ToggleBank
              </span>
              <span className="text-[9px] uppercase tracking-[0.2em] text-muted-foreground font-medium mt-0.5">
                Est. 1894
              </span>
            </div>
          </a>

          <nav className="hidden lg:flex items-center gap-1 text-[13px] font-medium">
            {NAV.map((item) => (
              <a
                key={item}
                href="#"
                className="px-3 py-2 rounded-md text-foreground/70 hover:text-foreground hover:bg-foreground/[0.04] transition-colors flex items-center gap-1"
              >
                {item}
                <ChevronDown className="w-3 h-3 opacity-50" strokeWidth={2.25} />
              </a>
            ))}
            <span className="mx-2 h-4 w-px bg-border" />
            <a
              href="#"
              className="px-3 py-2 rounded-md text-foreground font-semibold"
            >
              Help & support
            </a>
          </nav>
        </div>

        <div className="flex items-center gap-2">
          <button className="hidden sm:inline-flex items-center gap-2 px-3 py-2 rounded-md text-sm text-foreground/70 hover:text-foreground hover:bg-foreground/[0.04] transition-colors">
            <Search className="w-4 h-4" />
            <span className="hidden md:inline">Search</span>
          </button>
          <button className="hidden sm:inline-flex text-sm font-semibold px-4 py-2 rounded-md text-foreground hover:bg-foreground/[0.04] transition-colors">
            Open account
          </button>
          <button className="hidden sm:inline-flex bg-ink text-cream font-semibold text-sm px-4 py-2 rounded-md hover:bg-ink-2 transition-colors shadow-sm">
            Sign in
          </button>
          <button
            className="lg:hidden p-2 rounded-md hover:bg-foreground/[0.04] transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-border bg-background px-6 py-4 space-y-1 text-sm font-medium">
          {NAV.map((item) => (
            <a
              key={item}
              href="#"
              className="block py-2.5 text-foreground/80 hover:text-foreground"
            >
              {item}
            </a>
          ))}
          <a href="#" className="block py-2.5 text-foreground font-semibold">
            Help & support
          </a>
          <div className="pt-3 border-t border-border flex gap-2">
            <button className="flex-1 bg-ink text-cream font-semibold text-sm px-5 py-2.5 rounded-md">
              Sign in
            </button>
            <button className="flex-1 border border-border text-foreground font-semibold text-sm px-5 py-2.5 rounded-md">
              Open account
            </button>
          </div>
        </div>
      )}
    </header>
  );
};

export default BarclaysHeader;
