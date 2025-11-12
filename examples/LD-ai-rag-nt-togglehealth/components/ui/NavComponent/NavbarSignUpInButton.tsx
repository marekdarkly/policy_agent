import React from "react";
import { Button } from "@/components/ui/button";

export const NavbarSignUpButton = ({
    backgroundColor,
    textColor,
    onClick,
    ...props
}: {
    backgroundColor?: string;
    textColor?: string;
    className?: string;
    onClick?: () => void;
    props?: any;
}) => {
    return (
        <Button
            className={`cursor-pointer rounded-3xl w-[6rem] ${backgroundColor} ${textColor} shadow-lg hover:brightness-125`}

            onClick={onClick}
            {...props}
        >
            Join Now
        </Button>
    );
};

export const NavbarSignInButton = ({
    borderColor,
    backgroundColor,
}: {
    borderColor: string;
    backgroundColor: string;
}) => {
    return (
        <Button
            className={`rounded-3xl w-[6rem] border-2 hidden sm:block ${borderColor} bg-transparent ${backgroundColor} text-transparent bg-clip-text cursor-auto shadow-lg`}
        >
            Sign In
        </Button>
    );
};
