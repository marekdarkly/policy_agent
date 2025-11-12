import React from "react";
import { useRouter } from "next/router";
import { getCompanyLogos } from "@/utils/assetLoader";

const NavLogo = ({ srcHref, altText }: { srcHref?: string; altText?: string }) => {
  const router = useRouter();
  
  function goHome() {
    router.push("/");
  }
  
  // Get the appropriate logo based on altText or default to banking
  const getLogo = () => {
    if (srcHref) {
      return srcHref;
    }
    
    const industry = altText === 'health' ? 'health' : 
                    altText === 'mental-health' ? 'mental-health' :
                    altText === 'investment' ? 'investment' : 'banking';
    const logos = getCompanyLogos(industry);
    return logos.horizontal;
  };
  
  return (
    <div className="ml-2 sm:ml-8 flex cursor-pointer" id="navbar-logo" onClick={() => goHome()} title= "Go Home">
      <img src={getLogo()} alt={`${altText ? altText : "banking"} logo`} className="h-10 pr-2" />
    </div>
  );
};

export default NavLogo;
