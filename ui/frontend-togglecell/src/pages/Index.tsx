import { useState } from "react";
import SupportHeader from "@/components/SupportHeader";
import HeroSearch from "@/components/HeroSearch";
import FAQSection from "@/components/FAQSection";
import CategoryGrid from "@/components/CategoryGrid";
import ContactFooter from "@/components/ContactFooter";
import ChatWidget from "@/components/ChatWidget";
import Terminal from "@/components/Terminal";

const Index = () => {
  const [chatOpen, setChatOpen] = useState(true);
  const [initialQuery, setInitialQuery] = useState<string | undefined>();

  const handleSearch = (query: string) => {
    setInitialQuery(query);
    setChatOpen(true);
  };

  return (
    <div className="min-h-screen bg-background">
      <Terminal />
      <SupportHeader />
      <HeroSearch onSearch={handleSearch} />
      <FAQSection />
      <CategoryGrid />
      <ContactFooter />
      <ChatWidget
        isOpen={chatOpen}
        onClose={() => {
          setChatOpen(false);
          setInitialQuery(undefined);
        }}
        initialQuery={initialQuery}
      />
    </div>
  );
};

export default Index;
