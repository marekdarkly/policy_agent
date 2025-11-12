import { cn } from "@/utils/utils";
import React, { useState } from "react";
import Image from "next/image";
import arrow from "@/public/sidenav/arrow.svg";

export const CSCard = ({
  className,
  cardTitle,
  icon,
  iconHover,
  hoverBackground,
  noHoverBackground,
}: {
  className?: string;
  cardTitle: string;
  icon: any;
  iconHover: any;
  hoverBackground: any;
  noHoverBackground: any;
}) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className={cn(
        "relative card w-full p-4 rounded-2xl text-white font-sohned flex items-center py-7",
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <Image
        src={isHovered ? hoverBackground.src : noHoverBackground.src}
        alt="Background"
        className="rounded-2xl"
        fill
        sizes="100vw"
        style={{
          objectFit: "cover"
        }} />
      <div className="relative flex items-center justify-between w-full z-10">
        <Image
          src={isHovered ? iconHover.src : icon.src}
          alt={cardTitle}
          width={48}
          height={48}
          style={{
            maxWidth: "100%",
            width: "auto",
            height: "auto"
          }} />
        <p className="text-xl font-sohne flex-grow text-center mx-auto">{cardTitle}</p>
        <Image
          src={arrow.src}
          alt="Arrow"
          width={10}
          height={10}
          style={{
            objectFit: "fill"
          }} />
      </div>
    </div>
  );
};
