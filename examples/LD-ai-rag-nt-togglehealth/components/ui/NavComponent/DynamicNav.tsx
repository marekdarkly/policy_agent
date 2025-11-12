import React from "react";
import { type Industry } from "@/utils/industryAssets";
import BankNav from "./BankNav";
import HealthNav from "./HealthNav";
import MentalHealthNav from "./MentalHealthNav";

interface DynamicNavProps {
  industry: Industry;
}

const DynamicNav: React.FC<DynamicNavProps> = ({ industry }) => {
  switch (industry) {
    case "health":
      return <HealthNav />;
    case "mental-health":
      return <MentalHealthNav />;
    case "investment":
      return <BankNav />; // Using BankNav for investment for now
    case "banking":
    default:
      return <BankNav />;
  }
};

export default DynamicNav;
