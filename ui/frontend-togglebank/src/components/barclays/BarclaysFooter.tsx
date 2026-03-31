import { MessageCircle, Phone, MapPin } from "lucide-react";

interface BarclaysFooterProps {
  onChatOpen?: () => void;
}

const BarclaysFooter = ({ onChatOpen }: BarclaysFooterProps) => {
  return (
    <>
      {/* Contact CTA */}
      <section className="bg-[hsl(var(--barclays-dark))] py-14 md:py-16">
        <div className="container text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-3 tracking-tight">
            Can't find what you're looking for?
          </h2>
          <p className="text-white/70 mb-8 max-w-md mx-auto text-sm">
            Get in touch with us and we'll be happy to help.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={onChatOpen}
              className="inline-flex items-center justify-center gap-2 bg-white text-[hsl(var(--barclays-dark))] font-semibold px-8 py-3.5 rounded-sm hover:bg-white/90 transition-colors duration-200"
            >
              <MessageCircle className="w-5 h-5" />
              Chat with us
            </button>
            <button className="inline-flex items-center justify-center gap-2 bg-white/10 text-white border border-white/30 font-semibold px-8 py-3.5 rounded-sm hover:bg-white/20 transition-colors duration-200">
              <Phone className="w-5 h-5" />
              Call us
            </button>
            <button className="inline-flex items-center justify-center gap-2 bg-white/10 text-white border border-white/30 font-semibold px-8 py-3.5 rounded-sm hover:bg-white/20 transition-colors duration-200">
              <MapPin className="w-5 h-5" />
              Find a branch
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[hsl(var(--barclays-dark))] border-t border-white/10 py-10">
        <div className="container">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Personal Banking</h4>
              <ul className="space-y-2 text-sm text-white/50">
                <li><a href="#" className="hover:text-white/80 transition-colors">Current accounts</a></li>
                <li><a href="#" className="hover:text-white/80 transition-colors">Savings</a></li>
                <li><a href="#" className="hover:text-white/80 transition-colors">Mortgages</a></li>
                <li><a href="#" className="hover:text-white/80 transition-colors">Credit cards</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Ways to bank</h4>
              <ul className="space-y-2 text-sm text-white/50">
                <li><a href="#" className="hover:text-white/80 transition-colors">Online Banking</a></li>
                <li><a href="#" className="hover:text-white/80 transition-colors">Mobile banking</a></li>
                <li><a href="#" className="hover:text-white/80 transition-colors">Telephone banking</a></li>
                <li><a href="#" className="hover:text-white/80 transition-colors">Find a branch</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Help</h4>
              <ul className="space-y-2 text-sm text-white/50">
                <li><a href="#" className="hover:text-white/80 transition-colors">Help and support</a></li>
                <li><a href="#" className="hover:text-white/80 transition-colors">Contact us</a></li>
                <li><a href="#" className="hover:text-white/80 transition-colors">Accessibility</a></li>
                <li><a href="#" className="hover:text-white/80 transition-colors">Complaints</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-4">About ToggleBank</h4>
              <ul className="space-y-2 text-sm text-white/50">
                <li><a href="#" className="hover:text-white/80 transition-colors">About us</a></li>
                <li><a href="#" className="hover:text-white/80 transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-white/80 transition-colors">Sustainability</a></li>
                <li><a href="#" className="hover:text-white/80 transition-colors">Investor relations</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/10 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-full bg-[hsl(var(--barclays-primary))] flex items-center justify-center">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="text-white">
                  <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" fill="currentColor" opacity="0.9"/>
                  <path d="M12 6l-6 3v6l6 3 6-3V9l-6-3z" fill="currentColor"/>
                </svg>
              </div>
              <span className="text-xs text-white/40">
                © 2026 ToggleBank Ltd. Authorised by the PRA and regulated by the FCA and PRA.
              </span>
            </div>
            <div className="flex gap-4 text-xs text-white/40">
              <a href="#" className="hover:text-white/70 transition-colors">Privacy</a>
              <a href="#" className="hover:text-white/70 transition-colors">Cookies</a>
              <a href="#" className="hover:text-white/70 transition-colors">Terms</a>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
};

export default BarclaysFooter;
