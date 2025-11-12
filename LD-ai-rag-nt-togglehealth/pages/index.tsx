import { useContext } from "react";
import Head from "next/head";
import LoginContext from "@/utils/contexts/login";
import BankHomePage from "@/components/ui/bankcomponents/bankHomePage";
import BankUserDashboard from "@/components/ui/bankcomponents/bankUserDashboard";
import HealthHomePage from "@/components/ui/healthcomponents/healthHomePage";
import HealthUserDashboard from "@/components/ui/healthcomponents/healthUserDashboard";
import InvestmentHomePage from "@/components/ui/investmentcomponents/InvestmentHomePage";
import MentalHealthHomePage from "@/components/ui/mentalhealthcomponents/mentalHealthHomePage";
import MentalHealthUserDashboard from "@/components/ui/mentalhealthcomponents/mentalHealthUserDashboard";
import Chatbot from "@/components/chatbot/ChatBot";
import { getIndustryFromFlag, type Industry, getIndustryAssets } from "@/utils/industryAssets";

// Server-side function to get industry from LaunchDarkly
export async function getServerSideProps() {
  let industry: Industry = "banking"; // Default fallback
  
  try {
    // Use the server-side SDK key to get the flag value
    const response = await fetch(`${process.env.PYTHON_API_URL || 'http://localhost:8000'}/get-flag-value`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        flag_key: 'nt-toggle-rag-demo'
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('🔍 Server-side flag response:', data);
      if (data.flag_value) {
        industry = getIndustryFromFlag(data.flag_value);
        console.log('🔍 Server-side mapped industry:', industry);
      }
    } else {
      console.log('🔍 Server-side flag request failed:', response.status);
    }
  } catch (error) {
    console.error('🔍 Server-side error fetching flag value:', error);
    // For testing, let's hardcode to 'health' if backend is not available
    industry = "health";
  }
  
  console.log('🔍 Server-side final industry:', industry);
  
  return {
    props: {
      industry,
    },
  };
}

export default function Home({ industry }: { industry: Industry }) {
  const { isLoggedIn } = useContext(LoginContext);
  
  console.log('🔍 Server-side industry:', industry);
  
  const assets = getIndustryAssets(industry);
  console.log('🔍 Assets title:', assets.title);
  
  // Simple component selection
  const renderContent = () => {
    if (!isLoggedIn) {
      switch (industry) {
        case "health":
          return <HealthHomePage />;
        case "investment":
          return <InvestmentHomePage />;
        case "mental-health":
          return <MentalHealthHomePage />;
        default: // banking
          return <BankHomePage />;
      }
    } else {
      switch (industry) {
        case "health":
          return <HealthUserDashboard />;
        case "investment":
          return <BankUserDashboard />; // Using banking for now
        case "mental-health":
          return <MentalHealthUserDashboard />;
        default: // banking
          return <BankUserDashboard />;
      }
    }
  };
  
  return (
    <>
      <Head>
        <title>{assets.title}</title>
        <meta name="description" content={assets.description} />
      </Head>
      <main className={`w-full min-h-screen bg-cover bg-center bg-no-repeat pb-10`}>
        {renderContent()}
        <Chatbot />
      </main>
    </>
  );
}
