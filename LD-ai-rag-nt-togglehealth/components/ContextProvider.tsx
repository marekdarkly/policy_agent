import { ElementType, useEffect, useState } from "react";
import { setCookie } from "cookies-next";
import { LD_CONTEXT_COOKIE_KEY } from "@/utils/constants";
import { LDContextInterface } from "@/utils/typescriptTypesInterfaceLogin";
import { SyncLoader } from "react-spinners";
import { MultiKindLDContext } from "@/utils/MultiKindLDContext";
import { getLocation, getDeviceForContext } from "@/utils/utils";
import { v4 as uuidv4 } from "uuid";

// Simple provider that just renders children - no LaunchDarkly client-side needed
const SimpleProvider = ({ children }: { children: React.ReactNode }) => {
    return <>{children}</>;
};

const ContextProvider = ({ children }: { children: React.ReactNode }) => {
    const [ProviderComponent, setProviderComponent] = useState<ElementType>();

    useEffect(() => {
        const initializeProvider = async () => {
            // Set up context for server-side use only
            const context: LDContextInterface = MultiKindLDContext({
                isAnonymous: true,
                audienceKey: uuidv4().slice(0, 10),
                userRole: "",
                userTier: "",
                userName: "",
                userEmail: "",
                userKey: uuidv4().slice(0, 10),
                newDevice: getDeviceForContext(),
                newLocation: getLocation(),
            });

            setCookie(LD_CONTEXT_COOKIE_KEY, context);
            
            // Use simple provider - no client-side LaunchDarkly needed
            setProviderComponent(() => SimpleProvider);
        };

        initializeProvider();
    }, []);

    if (!ProviderComponent) {
        return <LoadingComponent />;
    }

    return <ProviderComponent>{children}</ProviderComponent>;
};

export default ContextProvider;

const LoadingComponent = () => {
    return (
        <div className="w-[100vw] h-[100vh] flex items-center justify-center">
            <div className="flex flex-col gap-y-8 items-center px-4">
                <h1 className="text-4xl text-center">Loading...</h1>
                <SyncLoader
                    className=""
                    size={30}
                    margin={20}
                    speedMultiplier={0.8}
                    color={"#405BFF"}
                />
            </div>
        </div>
    );
};
