export type Industry = 'banking' | 'health' | 'investment' | 'mental-health';

export interface IndustryAssets {
  logo: {
    horizontal: string;
    vertical: string;
  };
  backgrounds: {
    hero: string;
    dashboard: string;
  };
  icons: Record<string, string>;
  title: string;
  description: string;
}

export const getIndustryAssets = (industry: Industry): IndustryAssets => {
  switch (industry) {
    case 'mental-health':
      return {
        logo: {
          horizontal: '/mental-health/toggleMentalHealth_logo_horizontal.svg',
          vertical: '/mental-health/toggleMentalHealth_logo_vertical.svg'
        },
        backgrounds: {
          hero: '/mental-health/backgrounds/mental-health-hero-background-brain.svg',
          dashboard: '/mental-health/backgrounds/mental-health-dashboard-background-left.svg'
        },
        icons: {
          crisis: '/mental-health/icons/crisis.svg',
          therapy: '/mental-health/icons/therapy.svg',
          medication: '/mental-health/icons/medication.svg',
          wellness: '/mental-health/icons/wellness.svg',
          support: '/mental-health/icons/support.svg',
          resources: '/mental-health/icons/resources.svg'
        },
        title: 'Toggle Mental Health - Crisis Monitoring & Support Platform',
        description: 'Mental health crisis monitoring and support made simple with Toggle Mental Health. Trusted by mental health professionals and individuals worldwide.'
      };
    
    case 'health':
      return {
        logo: {
          horizontal: '/health/toggleHealth_logo_horizontal.svg',
          vertical: '/health/toggleHealth_logo_vertical.svg'
        },
        backgrounds: {
          hero: '/health/backgrounds/health-hero-background-heart.svg',
          dashboard: '/health/backgrounds/health-dashboard-background-left.svg'
        },
        icons: {
          insurance: '/health/icons/insurance.svg',
          pharmacy: '/health/icons/pharmacy.svg',
          telemedicine: '/health/icons/telemedicine.svg',
          wellness: '/health/icons/wellness.svg'
        },
        title: 'Toggle Health - Smart Healthcare Platform',
        description: 'Healthcare made simple with Toggle Health. Trusted by healthcare providers and patients worldwide.'
      };
    
    case 'investment':
      return {
        logo: {
          horizontal: '/investment/toggleInvestments_logo_horizontal.svg',
          vertical: '/investment/toggleInvestments_logo_vertical.svg'
        },
        backgrounds: {
          hero: '/investment/backgrounds/investment-hero-background-chart.svg',
          dashboard: '/investment/backgrounds/investment-dashboard-background-left.svg'
        },
        icons: {
          stocks: '/investment/icons/stocks.svg',
          bonds: '/investment/icons/bonds.svg',
          etfs: '/investment/icons/etfs.svg',
          crypto: '/investment/icons/crypto.svg'
        },
        title: 'Toggle Investments - Smart Investment Platform',
        description: 'Invest smart with Toggle Investments. More than 100,000 investors worldwide trust us with their portfolios.'
      };
    
    default: // banking
      return {
        logo: {
          horizontal: '/banking/toggleBank_logo_horizontal.svg',
          vertical: '/banking/toggleBank_logo_vertical.svg'
        },
        backgrounds: {
          hero: '/banking/backgrounds/bank-hero-background.svg',
          dashboard: '/banking/backgrounds/bank-dashboard-background-left.svg'
        },
        icons: {
          checking: '/banking/icons/checking.svg',
          savings: '/banking/icons/savings.svg',
          credit: '/banking/icons/credit.svg',
          mortgage: '/banking/icons/mortgage.svg'
        },
        title: 'Toggle Bank - Smart Banking Platform',
        description: 'Banking made simple with Toggle Bank. Trusted by millions of customers worldwide.'
      };
  }
};

export const getIndustryFromFlag = (flagValue: string): Industry => {
  // Map feature flag values to industries
  switch (flagValue?.toLowerCase()) {
    case 'mental-health':
    case 'mentalhealth':
    case 'crisis':
    case 'mental':
      return 'mental-health';
    case 'health':
    case 'healthcare':
    case 'medical':
      return 'health';
    case 'investment':
    case 'investing':
    case 'finance':
      return 'investment';
    case 'banking':
    case 'bank':
    default:
      return 'banking';
  }
};
