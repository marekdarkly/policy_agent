import { Search, User, Menu } from "lucide-react";
import { useState } from "react";

const SupportHeader = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-background border-b border-border">
      {/* Top bar */}
      <div className="bg-foreground">
        <div className="container flex items-center justify-between py-1.5 text-xs font-medium tracking-wide">
          <div className="flex gap-4">
            <button className="text-primary-foreground/90 hover:text-primary-foreground transition-colors">Personal</button>
            <button className="text-primary-foreground/50 hover:text-primary-foreground transition-colors">Business</button>
          </div>
          <div className="hidden sm:flex gap-4">
            <button className="text-primary-foreground/70 hover:text-primary-foreground transition-colors">Find a store</button>
            <button className="text-primary-foreground/70 hover:text-primary-foreground transition-colors">Network Status</button>
          </div>
        </div>
      </div>

      {/* Main nav */}
      <div className="container flex items-center justify-between h-16">
        <div className="flex items-center gap-8">
          <a href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">TC</span>
            </div>
            <span className="font-bold text-lg tracking-tight text-foreground">ToggleCell</span>
          </a>
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
            <a href="#" className="hover:text-foreground transition-colors">Phones & Devices</a>
            <a href="#" className="hover:text-foreground transition-colors">SIM Only</a>
            <a href="#" className="hover:text-foreground transition-colors">Broadband</a>
            <a href="#" className="text-primary font-semibold">Support</a>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <button className="p-2 rounded-full hover:bg-secondary transition-colors">
            <Search className="w-5 h-5 text-muted-foreground" />
          </button>
          <button className="p-2 rounded-full hover:bg-secondary transition-colors">
            <User className="w-5 h-5 text-muted-foreground" />
          </button>
          <button
            className="md:hidden p-2 rounded-full hover:bg-secondary transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <Menu className="w-5 h-5 text-muted-foreground" />
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-border bg-background px-6 py-4 space-y-3 text-sm font-medium">
          <a href="#" className="block text-muted-foreground hover:text-foreground">Phones & Devices</a>
          <a href="#" className="block text-muted-foreground hover:text-foreground">SIM Only</a>
          <a href="#" className="block text-muted-foreground hover:text-foreground">Broadband</a>
          <a href="#" className="block text-primary font-semibold">Support</a>
        </div>
      )}
    </header>
  );
};

export default SupportHeader;
