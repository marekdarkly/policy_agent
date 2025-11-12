export type LoginUserFunctionType = (email: string) => Promise<void>;

//TODO: need to extend user type or something into here or vice versa
export interface Persona {
    personaname: string;
    personatier: string;
    personaimage: string;
    personaemail: string;
    personarole: string;
}

export interface LoginContextProviderInterface {
    userObject: Persona;
    isLoggedIn: boolean;
    updateAudienceContext: () => Promise<void>;
    updateRandomizedUserContext: () => Promise<void>;
    loginUser: LoginUserFunctionType;
    logoutUser: () => Promise<void>;
    allUsers: Persona[];
    appMultiContext: {};
}

export interface LDContextInterface {
    audience: AudienceInterface;
    device: DeviceInterface;
    kind: "multi" | string;
    location: LocationInterface;
    user: UserInterface;
}

export interface LocationInterface {
    continent: string;
    key: string;
    city: string;
    timeZone: string;
}

export interface UserInterface {
    anonymous: boolean;
    key: string;
    role: string;
    tier: string;
    name: string;
    email: string;
}

export interface DeviceInterface {
    key: DeviceType;
    name: DeviceType;
    operating_system: OperatingSystemType;
    platform: DeviceType;
}

export interface AudienceInterface{
    key: string
}

export type DeviceType = "" | "Mobile" | "Desktop";
export type OperatingSystemType = "Android" | "iOS" | "Windows" | "macOS" | "";
