import React, { createContext, useContext, ReactNode } from 'react';
import { Industry, getIndustryFromFlag, getIndustryAssets } from '@/utils/industryAssets';

interface IndustryContextType {
  industry: Industry;
  assets: ReturnType<typeof getIndustryAssets>;
  flagValue: string;
}

const IndustryContext = createContext<IndustryContextType | undefined>(undefined);

export const useIndustry = () => {
  const context = useContext(IndustryContext);
  if (context === undefined) {
    throw new Error('useIndustry must be used within an IndustryProvider');
  }
  return context;
};

interface IndustryProviderProps {
  children: ReactNode;
}

export const IndustryProvider: React.FC<IndustryProviderProps> = ({ children }) => {
  // Simple config-based approach - can be changed via environment variable or config
  const flagValue = process.env.NEXT_PUBLIC_INDUSTRY || "banking";
  const industry = getIndustryFromFlag(flagValue);
  const assets = getIndustryAssets(industry);
  
  console.log('🔍 IndustryContext - Using industry:', flagValue);
  console.log('🔍 IndustryContext - Mapped industry:', industry);
  console.log('🔍 IndustryContext - Assets title:', assets.title);
  
    const value: IndustryContextType = {
    industry,
    assets,
    flagValue
  };
  
  return (
    <IndustryContext.Provider value={value}>
      {children}
    </IndustryContext.Provider>
  );
};
