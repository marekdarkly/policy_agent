import { Search, Menu, X } from "lucide-react";
import { useState } from "react";

const BarclaysHeader = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-background border-b border-border">
      <div className="container flex items-center justify-between h-14">
        {/* Logo + nav */}
        <div className="flex items-center gap-8">
          <a href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-[hsl(var(--barclays-primary))] flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="text-white">
                <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" fill="currentColor" opacity="0.9"/>
                <path d="M12 6l-6 3v6l6 3 6-3V9l-6-3z" fill="currentColor"/>
              </svg>
            </div>
            <span className="font-bold text-lg tracking-tight text-[hsl(var(--barclays-primary))]">ToggleBank</span>
          </a>

          <nav className="hidden lg:flex items-center gap-1 text-sm font-medium">
            {["Accounts", "Mortgages", "Loans", "Credit cards", "Savings"].map((item) => (
              <a key={item} href="#" className="px-3 py-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
                {item}
              </a>
            ))}
            <a href="#" className="px-3 py-1.5 rounded-md text-[hsl(var(--barclays-primary))] font-semibold bg-[hsl(var(--barclays-primary))]/5">
              Help & support
            </a>
          </nav>
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-1.5">
          <button className="p-2 rounded-md hover:bg-secondary transition-colors">
            <Search className="w-4.5 h-4.5 text-muted-foreground" />
          </button>
          <button className="hidden sm:inline-flex bg-[hsl(var(--barclays-primary))] text-white font-semibold text-sm px-4 py-1.5 rounded-md hover:bg-[hsl(var(--barclays-dark))] transition-colors">
            Log In
          </button>
          <button
            className="lg:hidden p-2 rounded-md hover:bg-secondary transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-5 h-5 text-muted-foreground" /> : <Menu className="w-5 h-5 text-muted-foreground" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-border bg-background px-6 py-4 space-y-2 text-sm font-medium">
          {["Accounts", "Mortgages", "Loans", "Credit cards", "Savings"].map((item) => (
            <a key={item} href="#" className="block py-2 text-muted-foreground hover:text-foreground">{item}</a>
          ))}
          <a href="#" className="block py-2 text-[hsl(var(--barclays-primary))] font-semibold">Help & support</a>
          <div className="pt-3 border-t border-border">
            <button className="bg-[hsl(var(--barclays-primary))] text-white font-semibold text-sm px-5 py-2 rounded-md w-full">Log In</button>
          </div>
        </div>
      )}
    </header>
  );
};

export default BarclaysHeader;
