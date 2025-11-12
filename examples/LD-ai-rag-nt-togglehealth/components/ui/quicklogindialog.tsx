import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogClose,
} from "@/components/ui/dialog";
import { useContext } from "react";
import LoginContext from "@/utils/contexts/login";
import { capitalizeFirstLetter } from "@/utils/utils";
import type { Persona } from "@/utils/typescriptTypesInterfaceLogin";

export function QuickLoginDialog() {
    const { loginUser, isLoggedIn, userObject, allUsers } = useContext(LoginContext);
    const personaClicked = (persona: Persona): void => {
        loginUser(persona.personaemail);
    };

    return (
        <>
            <Dialog>
                <DialogTrigger
                    className={`w-full p-2 rounded-none text-xl border-2  text-black  border-loginComponentBlue  hover:text-white hover:bg-gray-800`}
                >
                    {isLoggedIn ? "Quick Login" : "Switch SSO User"}
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle className="mb-4">
                            {isLoggedIn ? "Quick Login SSO User" : "Switch SSO User"}
                        </DialogTitle>
                        <div className="overflow-y-auto h-64">
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-x-4 gap-y-6 justify-items-center py-4">
                                {allUsers
                                    ?.filter(
                                        (persona: Persona) =>
                                            persona.personaname !== userObject.personaname
                                    )
                                    .map((persona: Persona, index: number) => (
                                        <DialogClose key={index}>
                                            <div
                                                className="flex flex-col items-center cursor-pointer flex-shrink-0 hover:brightness-125 text-md font-sohnelight gap-y-2 text-center"
                                                onClick={() => personaClicked(persona)}
                                            >
                                                <img
                                                    src={persona.personaimage}
                                                    className="w-20 h-20 rounded-full shadow-xl"
                                                    alt={persona.personaname}
                                                />
                                                <p className="">{persona.personaname}</p>
                                                <p className="">{persona.personaemail}</p>
                                                <p className="">Role: {persona.personarole}</p>
                                                <p className="">
                                                    {capitalizeFirstLetter(persona.personatier)}{" "}
                                                    Tier
                                                </p>
                                            </div>
                                        </DialogClose>
                                    ))}
                            </div>
                        </div>
                    </DialogHeader>
                </DialogContent>
            </Dialog>
        </>
    );
}
