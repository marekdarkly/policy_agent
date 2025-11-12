import React from "react";

const NavLinkButton = ({
  text,
  index,
  navLinkColor,
  href,
}: {
  text: string;
  index: number;
  href: string;
  navLinkColor: string;
}) => {
  return (
    <button
      className={`cursor-default hidden sm:block bg-transparent pb-[3rem] items-start text-base font-sohnelight font-medium transition-colors bg-no-repeat bg-bottom bg-[length:100%_3px] 
                  ${
                    index === 0
                      ? `text-navlink hover:text-navbarlightgrey hover:bg-${navLinkColor} bg-${navLinkColor} outline-none`
                      : `text-navlink  hover:text-navbarlightgrey hover:bg-${navLinkColor}`
                  }`}
    >
      <a href={href}> {text}</a>
    </button>
  );
};

export default NavLinkButton;
