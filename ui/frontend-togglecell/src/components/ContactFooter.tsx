import { MessageCircle, Phone, Mail } from "lucide-react";

const ContactFooter = () => {
  return (
    <>
      {/* Contact CTA */}
      <section className="bg-primary py-16 md:py-20">
        <div className="container text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-primary-foreground mb-3 tracking-tight">
            Still can't find what you're looking for?
          </h2>
          <p className="text-primary-foreground/80 mb-8 max-w-md mx-auto">
            Contact us through the ToggleCell app or reach out directly.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="inline-flex items-center justify-center gap-2 bg-primary-foreground text-primary font-semibold px-8 py-3.5 rounded-sm hover:bg-primary-foreground/90 transition-colors duration-200 ease-premium">
              <MessageCircle className="w-5 h-5" />
              Live Chat
            </button>
            <button className="inline-flex items-center justify-center gap-2 bg-primary-foreground/10 text-primary-foreground border border-primary-foreground/30 font-semibold px-8 py-3.5 rounded-sm hover:bg-primary-foreground/20 transition-colors duration-200 ease-premium">
              <Phone className="w-5 h-5" />
              Call Us
            </button>
            <button className="inline-flex items-center justify-center gap-2 bg-primary-foreground/10 text-primary-foreground border border-primary-foreground/30 font-semibold px-8 py-3.5 rounded-sm hover:bg-primary-foreground/20 transition-colors duration-200 ease-premium">
              <Mail className="w-5 h-5" />
              Email Support
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-foreground py-12">
        <div className="container">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-10">
            <div>
              <h4 className="text-sm font-semibold text-primary-foreground mb-4">Help & Support</h4>
              <ul className="space-y-2.5 text-sm text-primary-foreground/60">
                <li><a href="#" className="hover:text-primary-foreground transition-colors">All help topics</a></li>
                <li><a href="#" className="hover:text-primary-foreground transition-colors">Device guides</a></li>
                <li><a href="#" className="hover:text-primary-foreground transition-colors">Lost or stolen</a></li>
                <li><a href="#" className="hover:text-primary-foreground transition-colors">Contact us</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-primary-foreground mb-4">Shop</h4>
              <ul className="space-y-2.5 text-sm text-primary-foreground/60">
                <li><a href="#" className="hover:text-primary-foreground transition-colors">Pay monthly</a></li>
                <li><a href="#" className="hover:text-primary-foreground transition-colors">Pay as you go</a></li>
                <li><a href="#" className="hover:text-primary-foreground transition-colors">SIM only</a></li>
                <li><a href="#" className="hover:text-primary-foreground transition-colors">Broadband</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-primary-foreground mb-4">About</h4>
              <ul className="space-y-2.5 text-sm text-primary-foreground/60">
                <li><a href="#" className="hover:text-primary-foreground transition-colors">About us</a></li>
                <li><a href="#" className="hover:text-primary-foreground transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-primary-foreground transition-colors">News</a></li>
                <li><a href="#" className="hover:text-primary-foreground transition-colors">Accessibility</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-primary-foreground mb-4">Legal</h4>
              <ul className="space-y-2.5 text-sm text-primary-foreground/60">
                <li><a href="#" className="hover:text-primary-foreground transition-colors">Terms & conditions</a></li>
                <li><a href="#" className="hover:text-primary-foreground transition-colors">Privacy policy</a></li>
                <li><a href="#" className="hover:text-primary-foreground transition-colors">Cookie policy</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-primary-foreground/10 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-[10px]">TC</span>
              </div>
              <span className="text-xs text-primary-foreground/40">
                © 2026 ToggleCell Ltd. All rights reserved.
              </span>
            </div>
            <div className="flex gap-4 text-xs text-primary-foreground/40">
              <a href="#" className="hover:text-primary-foreground/70 transition-colors">Site map</a>
              <a href="#" className="hover:text-primary-foreground/70 transition-colors">Privacy</a>
              <a href="#" className="hover:text-primary-foreground/70 transition-colors">Cookies</a>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
};

export default ContactFooter;
