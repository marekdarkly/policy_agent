import { useState } from "react";
import BarclaysHeader from "@/components/barclays/BarclaysHeader";
import BarclaysHero from "@/components/barclays/BarclaysHero";
import BarclaysQuickActions from "@/components/barclays/BarclaysQuickActions";
import BarclaysPopularQuestions from "@/components/barclays/BarclaysPopularQuestions";
import BarclaysTopics from "@/components/barclays/BarclaysTopics";
import BarclaysWaysToBank from "@/components/barclays/BarclaysWaysToBank";
import BarclaysServiceStatus from "@/components/barclays/BarclaysServiceStatus";
import BarclaysSecurityBanner from "@/components/barclays/BarclaysSecurityBanner";
import BarclaysMoreHelp from "@/components/barclays/BarclaysMoreHelp";
import BarclaysFooter from "@/components/barclays/BarclaysFooter";
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
    <div className="min-h-screen bg-background barclays-theme">
      <Terminal />
      <BarclaysHeader />
      <BarclaysHero onSearch={handleSearch} />
      <BarclaysQuickActions />
      <BarclaysPopularQuestions onQuestionClick={handleSearch} />
      <BarclaysTopics />
      <BarclaysWaysToBank />
      <BarclaysServiceStatus />
      <BarclaysSecurityBanner />
      <BarclaysMoreHelp />
      <BarclaysFooter onChatOpen={() => setChatOpen(true)} />
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
