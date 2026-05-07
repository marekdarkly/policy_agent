import { Search, Menu, X, ChevronDown, Check } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useDemoUser, DEMO_USERS, type DemoUserId } from "@/lib/demoUser";

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
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const { user, setUser } = useDemoUser();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!userMenuOpen) return;
    const onClick = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setUserMenuOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [userMenuOpen]);

  const pickUser = (id: DemoUserId) => {
    setUser(id);
    setUserMenuOpen(false);
  };

  const badgeClass = (id: DemoUserId) =>
    id === "internal"
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : "bg-blue-50 text-blue-700 border-blue-200";

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

          {/* Demo "fake login" — clicking the user pill opens a dropdown
              with the two presets. Each option drives LaunchDarkly user-key
              targeting (marek-internal-dev / marek-commercial-plan). */}
          <div className="hidden sm:block relative" ref={userMenuRef}>
            <button
              type="button"
              onClick={() => setUserMenuOpen((open) => !open)}
              aria-haspopup="menu"
              aria-expanded={userMenuOpen}
              title={`LaunchDarkly user_key: ${user.userKey}`}
              className="inline-flex items-center gap-2 px-2 py-1 rounded-full border border-border bg-background/70 hover:bg-foreground/[0.04] transition-colors"
            >
              <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-ink text-cream text-xs font-semibold">
                {user.name.charAt(0)}
              </span>
              <span className="text-sm font-semibold text-foreground hidden md:inline">
                {user.name}
              </span>
              <span
                className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${badgeClass(user.id)}`}
              >
                {user.badge}
              </span>
              <ChevronDown
                className={`w-3.5 h-3.5 opacity-60 transition-transform ${userMenuOpen ? "rotate-180" : ""}`}
                strokeWidth={2.25}
              />
            </button>

            {userMenuOpen && (
              <div
                role="menu"
                className="absolute right-0 mt-2 w-72 rounded-xl border border-border bg-background shadow-lg z-50 overflow-hidden"
              >
                <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground border-b border-border">
                  Switch demo user
                </div>
                {(Object.values(DEMO_USERS) as Array<typeof DEMO_USERS[DemoUserId]>).map((opt) => {
                  const isActive = opt.id === user.id;
                  return (
                    <button
                      key={opt.id}
                      role="menuitemradio"
                      aria-checked={isActive}
                      type="button"
                      onClick={() => pickUser(opt.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors ${
                        isActive ? "bg-foreground/[0.04]" : "hover:bg-foreground/[0.04]"
                      }`}
                    >
                      <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-ink text-cream text-sm font-semibold">
                        {opt.name.charAt(0)}
                      </span>
                      <span className="flex-1 min-w-0">
                        <span className="block text-sm font-semibold text-foreground truncate">
                          {opt.name}
                        </span>
                        <span
                          className={`inline-flex items-center mt-0.5 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${badgeClass(opt.id)}`}
                        >
                          {opt.badge}
                        </span>
                      </span>
                      {isActive && (
                        <Check className="w-4 h-4 text-foreground/70" strokeWidth={2.25} />
                      )}
                    </button>
                  );
                })}
                <div className="px-3 py-2 text-[10px] text-muted-foreground border-t border-border font-mono">
                  user_key: {user.userKey}
                </div>
              </div>
            )}
          </div>
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
          <div className="pt-3 border-t border-border space-y-1">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground pb-1">
              Switch demo user
            </div>
            {(Object.values(DEMO_USERS) as Array<typeof DEMO_USERS[DemoUserId]>).map((opt) => {
              const isActive = opt.id === user.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => {
                    setUser(opt.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 px-2 py-2.5 rounded-md text-left ${
                    isActive ? "bg-foreground/[0.06]" : "hover:bg-foreground/[0.04]"
                  }`}
                >
                  <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-ink text-cream text-sm font-semibold">
                    {opt.name.charAt(0)}
                  </span>
                  <span className="flex-1 min-w-0">
                    <span className="block text-sm font-semibold text-foreground">
                      {opt.name}
                    </span>
                    <span
                      className={`inline-flex items-center mt-0.5 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${badgeClass(opt.id)}`}
                    >
                      {opt.badge}
                    </span>
                  </span>
                  {isActive && (
                    <Check className="w-4 h-4 text-foreground/70" strokeWidth={2.25} />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </header>
  );
};

export default BarclaysHeader;
