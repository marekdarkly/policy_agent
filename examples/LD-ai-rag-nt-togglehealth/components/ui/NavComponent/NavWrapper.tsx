import React, { ReactElement } from "react";
import { cn } from "@/utils/utils";

const NavWrapper = ({ children, className }: { children: ReactElement, className?: string }) => {
  return (
    <nav className={cn("w-full bg-transparent font-audimat transition-all duration-150 py-6", className)}>
      <div className=" xl:mx-auto max-w-7xl flex">{children}</div>
    </nav>
  );
};

export default NavWrapper;
