export type Industry = 'banking' | 'health' | 'investment' | 'mental-health';

export interface CompanyLogos {
  vertical: string;
  horizontal: string;
}

export interface IndustryAssets {
  logos: CompanyLogos;
  backgrounds: {
    hero: {
      creditcard: string;
      dollarsign: string;
    };
    homepage: {
      left: string;
      right: string;
      specialOffer: string;
      retirement: string;
    };
  };
  icons: {
    checking: string;
    checkingOnHover: string;
    credit: string;
    creditOnHover: string;
    mortgage: string;
    mortgageOnHover: string;
    business: string;
    businessOnHover: string;
    savings: string;
    savingsOnHover: string;
  };
}

export const getIndustryAssets = (industry: Industry): IndustryAssets => {
  const basePath = `/${industry}`;
  
  // Get the correct file naming pattern based on industry
  const getBackgroundPaths = () => {
    switch (industry) {
      case 'banking':
        return {
          hero: {
            creditcard: `${basePath}/backgrounds/bank-hero-background-creditcard.svg`,
            dollarsign: `${basePath}/backgrounds/bank-hero-background-dollarsign.svg`,
          },
          homepage: {
            left: `${basePath}/backgrounds/bank-homepage-background-left.svg`,
            right: `${basePath}/backgrounds/bank-homepage-background-right.svg`,
            specialOffer: `${basePath}/backgrounds/bank-homepage-specialoffer-background.svg`,
            retirement: `${basePath}/backgrounds/bank-homepage-retirement-card-background.svg`,
          },
        };
      case 'health':
        return {
          hero: {
            creditcard: `${basePath}/backgrounds/health-hero-background-heart.svg`,
            dollarsign: `${basePath}/backgrounds/health-hero-background-heart.svg`,
          },
          homepage: {
            left: `${basePath}/backgrounds/health-dashboard-background-left.svg`,
            right: `${basePath}/backgrounds/health-dashboard-background-right.svg`,
            specialOffer: `${basePath}/backgrounds/health-dashboard-background-left.svg`,
            retirement: `${basePath}/backgrounds/health-dashboard-background-left.svg`,
          },
        };
      case 'mental-health':
        return {
          hero: {
            creditcard: `${basePath}/backgrounds/mental-health-hero-background-brain.svg`,
            dollarsign: `${basePath}/backgrounds/mental-health-hero-background-brain.svg`,
          },
          homepage: {
            left: `${basePath}/backgrounds/mental-health-dashboard-background-left.svg`,
            right: `${basePath}/backgrounds/mental-health-dashboard-background-right.svg`,
            specialOffer: `${basePath}/backgrounds/mental-health-dashboard-background-left.svg`,
            retirement: `${basePath}/backgrounds/mental-health-dashboard-background-left.svg`,
          },
        };
      default: // investment
        return {
          hero: {
            creditcard: `${basePath}/backgrounds/investment-hero-background-chart.svg`,
            dollarsign: `${basePath}/backgrounds/investment-hero-background-portfolio.svg`,
          },
          homepage: {
            left: `${basePath}/backgrounds/investment-homepage-background-left.svg`,
            right: `${basePath}/backgrounds/investment-homepage-background-right.svg`,
            specialOffer: `${basePath}/backgrounds/investment-homepage-specialoffer-background.svg`,
            retirement: `${basePath}/backgrounds/investment-homepage-retirement-card-background.svg`,
          },
        };
    }
  };
  
  // Get the correct logo naming pattern based on industry
  const getLogoPaths = () => {
    switch (industry) {
      case 'banking':
        return {
          vertical: `${basePath}/toggleBank_logo_vertical.svg`,
          horizontal: `${basePath}/toggleBank_logo_horizontal_black.svg`,
        };
      case 'health':
        return {
          vertical: `${basePath}/toggleHealth_logo_vertical.svg`,
          horizontal: `${basePath}/toggleHealth_logo_horizontal.svg`,
        };
      case 'mental-health':
        return {
          vertical: `${basePath}/toggleMentalHealth_logo_vertical.svg`,
          horizontal: `${basePath}/toggleMentalHealth_logo_horizontal.svg`,
        };
      default: // investment
        return {
          vertical: `${basePath}/toggleInvestments_logo_vertical.svg`,
          horizontal: `${basePath}/toggleInvestments_logo_horizontal.svg`,
        };
    }
  };
  
  // Get the correct icon paths based on industry
  const getIconPaths = () => {
    switch (industry) {
      case 'banking':
        return {
          checking: `${basePath}/icons/checking.svg`,
          checkingOnHover: `${basePath}/icons/checking-on-hover.svg`,
          credit: `${basePath}/icons/creditcard.svg`,
          creditOnHover: `${basePath}/icons/creditcard-on-hover.svg`,
          mortgage: `${basePath}/icons/mortgage.svg`,
          mortgageOnHover: `${basePath}/icons/mortgage-on-hover.svg`,
          business: `${basePath}/icons/business.svg`,
          businessOnHover: `${basePath}/icons/business-on-hover.svg`,
          savings: `${basePath}/icons/savings.svg`,
          savingsOnHover: `${basePath}/icons/savings-on-hover.svg`,
        };
      case 'health':
        return {
          checking: `${basePath}/icons/telemedicine.svg`,
          checkingOnHover: `${basePath}/icons/telemedicine-on-hover.svg`,
          credit: `${basePath}/icons/prescriptions.svg`,
          creditOnHover: `${basePath}/icons/prescriptions-on-hover.svg`,
          mortgage: `${basePath}/icons/pharmacy.svg`,
          mortgageOnHover: `${basePath}/icons/pharmacy-on-hover.svg`,
          business: `${basePath}/icons/insurance.svg`,
          businessOnHover: `${basePath}/icons/insurance-on-hover.svg`,
          savings: `${basePath}/icons/wellness.svg`,
          savingsOnHover: `${basePath}/icons/wellness-on-hover.svg`,
        };
      default: // investment
        return {
          checking: `${basePath}/icons/stocks.svg`,
          checkingOnHover: `${basePath}/icons/stocks-on-hover.svg`,
          credit: `${basePath}/icons/bonds.svg`,
          creditOnHover: `${basePath}/icons/bonds-on-hover.svg`,
          mortgage: `${basePath}/icons/etfs.svg`,
          mortgageOnHover: `${basePath}/icons/etfs-on-hover.svg`,
          business: `${basePath}/icons/portfolio.svg`,
          businessOnHover: `${basePath}/icons/portfolio-on-hover.svg`,
          savings: `${basePath}/icons/retirement.svg`,
          savingsOnHover: `${basePath}/icons/retirement-on-hover.svg`,
        };
    }
  };

  return {
    logos: getLogoPaths(),
    backgrounds: getBackgroundPaths(),
    icons: getIconPaths(),
  };
};

// Helper function to get just the logos
export const getCompanyLogos = (industry: Industry): CompanyLogos => {
  return getIndustryAssets(industry).logos;
};
