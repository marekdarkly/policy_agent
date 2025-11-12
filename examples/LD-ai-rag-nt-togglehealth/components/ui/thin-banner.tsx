"use client"

import React from "react"
import { X } from "lucide-react"
import Image from "next/image"
import { cn } from "@/utils/utils"


interface ImageProps {
  src: string
  alt: string
}

interface ThinBannerProps extends React.HTMLAttributes<HTMLDivElement> {
  text: string
  variant?: "default" | "info" | "warning" | "success" | "error"
  showCloseButton?: boolean
  onClose?: () => void
  action?: React.ReactNode
  sticky?: boolean
  image?: string | ImageProps
  imagePosition?: "left" | "right"
  imageSize?: number
}

export function ThinBanner({
  text,
  variant = "default",
  showCloseButton = true,
  onClose,
  action,
  sticky = false,
  image,
  imagePosition = "left",
  imageSize = 24,
  className,
  ...props
}: ThinBannerProps) {
  const [isVisible, setIsVisible] = React.useState(true)

  const handleClose = () => {
    setIsVisible(false)
    onClose?.()
  }

  if (!isVisible) return null

  const variantStyles = {
    default: "bg-primary text-primary-foreground",
    info: "bg-blue-500 text-white",
    warning: "bg-amber-500 text-white",
    success: "bg-green-500 text-white",
    error: "bg-red-500 text-white",
  }

  const imageSrc = typeof image === "string" ? image : image?.src
  const imageAlt = typeof image === "string" ? "Banner image" : image?.alt || "Banner image"

  return (
    <div
      className={cn(
        "relative w-full py-2 px-4 text-sm",
        variantStyles[variant],
        sticky && "sticky top-0 z-50",
        className,
      )}
      {...props}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <div className={cn("flex items-center gap-x-3", imagePosition === "right" && "flex-row-reverse")}>
          {image && (
            <div className="flex-shrink-0">
              <Image
                src={imageSrc! || "/placeholder.svg"}
                alt={imageAlt}
                width={imageSize}
                height={imageSize}
                className="object-contain"
              />
            </div>
          )}
          <p>{text}</p>
          {action && <div className={cn(imagePosition === "right" ? "mr-2" : "ml-2")}>{action}</div>}
        </div>
        {showCloseButton && (
          <button
            onClick={handleClose}
            className="ml-2 rounded-full p-1 hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
            aria-label="Close banner"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}

