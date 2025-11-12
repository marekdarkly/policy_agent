import { v4 as uuidv4 } from "uuid";
import { getDeviceForContext, getLocation } from "./utils";
import {
    LDContextInterface,
    DeviceInterface,
    LocationInterface,
} from "@/utils/typescriptTypesInterfaceLogin";
import { PERSONA_TIER_STANARD, PERSONA_ROLE_USER } from "@/utils/constants";

export const MultiKindLDContext = ({
    audienceKey = uuidv4().slice(0, 10),
    userRole = PERSONA_ROLE_USER,
    userTier = PERSONA_TIER_STANARD,
    userName = "",
    userEmail = "",
    isAnonymous = true,
    userKey = uuidv4().slice(0, 10),
    newDevice = getDeviceForContext(),
    newLocation = getLocation(),
}: {
    audienceKey?: string;
    userRole?: string;
    userTier?: string;
    userName?: string;
    userEmail?: string;
    isAnonymous: boolean;
    userKey?: string;
    newDevice?: DeviceInterface;
    newLocation?: LocationInterface;
}): LDContextInterface => {
    return {
        kind: "multi",
        user: {
            anonymous: isAnonymous,
            key: userKey, 
            role: isAnonymous ? "" : userRole,
            tier: isAnonymous ? "" : userTier,
            name: isAnonymous ? "" : userName,
            email: isAnonymous ? "" : userEmail,
        },
        
        device: newDevice,
        location: newLocation,

        audience: {
            key: audienceKey,
        },
    };
};
