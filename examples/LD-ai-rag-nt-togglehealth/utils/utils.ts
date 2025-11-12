import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { isAndroid, isIOS, isBrowser, isMobile, isMacOs, isWindows } from "react-device-detect";
import {
    LD_CONTEXT_COOKIE_KEY,
    ANDROID,
    IOS,
    DESKTOP,
    MOBILE,
    WINDOWS,
    MACOS,
    PERSONA_TIER_PLATINUM,
    PERSONA_TIER_STANARD,
    PERSONA_ROLE_BETA,
    PERSONA_ROLE_DEVELOPER,
    PERSONA_ROLE_USER,
    STARTER_PERSONAS
} from "./constants";
import { getCookie } from "cookies-next";
import {
    LocationInterface,
    DeviceInterface,
    DeviceType,
    OperatingSystemType,
} from "./typescriptTypesInterfaceLogin";
import { ALL_TIME_ZONES } from "./AllTimeZones";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function capitalizeFirstLetter(string: string) {
    return string?.charAt(0).toUpperCase() + string?.slice(1);
}

export function truncateString(str: string, num: number) {
    // If the length of str is less than or equal to num
    // just return str--don't truncate it.
    if (str?.length <= num) {
        return str;
    }
    // Return str truncated with '...' concatenated to the end of str.
    return str?.slice(0, num) + "...";
}

export const formatMoneyTrailingZero = (number: number) => {
    const splitNum = number.toString().split(".");
    const firstNum = splitNum[0];
    let secondNum = splitNum[1];

    if (secondNum === undefined) secondNum = "0";
    if (secondNum?.length === 2 && secondNum?.includes("0")) return number;
    if (secondNum?.length === 2) return number;
    return `${firstNum}.${secondNum}0`;
};

export function handleAlert({
    response,
    alert,
    type,
    message,
    callback,
    timeout,
}: {
    response: any;
    alert: any;
    type: any;
    message: any;
    callback: any;
    timeout: any;
}) {
    //to not allow multiple message pop up at the same time
    const alertTemplateEle = document
        ?.querySelector(".alert-template")
        ?.querySelector("#banner-message")?.innerHTML;
    if (alertTemplateEle === message) return;

    if (response instanceof Error && alert?.error) {
        return alert?.error(response.message);
    }

    if (alert?.show)
        alert?.show(message, {
            type,
            timeout: timeout ? timeout : 3000,
        });

    setTimeout(() => {
        if (callback) {
            callback();
        }
    }, 3000);
}

export function wait(seconds: number) {
    return new Promise((resolve) => {
        setTimeout(resolve, seconds * 1000);
    });
}

export const randomLatency = (min: number, max: number) =>
    max === undefined ? Math.random() * min : min + Math.random() * (max - min + 1);

export function delay(low: number, high: number) {
    const min = low * 1000;
    const max = high * 1000;
    const randomDelay = Math.floor(Math.random() * (max - min + 1)) + min;
    //console.log("Delay is: "+randomDelay)
    return new Promise((resolve) => setTimeout(resolve, randomDelay));
}

export const getOperatingSystem = (): OperatingSystemType => {
    if (isAndroid) return ANDROID;
    if (isIOS) return IOS;
    if (isWindows) return WINDOWS;
    if (isMacOs) return MACOS;
    return "";
};

export const getRandomizedOperatingSystem = (randomizedDevice: DeviceType): OperatingSystemType => {
    const mobileOS: OperatingSystemType[] = [ANDROID, IOS];
    const desktopOS: OperatingSystemType[] = [WINDOWS, MACOS];
    if (randomizedDevice.includes(MOBILE)) {
        return mobileOS[Math.floor(Math.random() * mobileOS.length)];
    }

    if (randomizedDevice.includes(DESKTOP)) {
        return desktopOS[Math.floor(Math.random() * desktopOS.length)];
    }
    return "";
};

export const getRandomizedUserTier = () => {
    const userTierArr = [PERSONA_TIER_PLATINUM, PERSONA_TIER_STANARD];

    return userTierArr[Math.floor(Math.random() * userTierArr.length)];
};

export const getRandomizedUserRole = () => {
    const userRoleArr = [PERSONA_ROLE_BETA, PERSONA_ROLE_DEVELOPER, PERSONA_ROLE_USER];

    return userRoleArr[Math.floor(Math.random() * userRoleArr.length)];
};

export const getDevice = (): DeviceType => {
    if (isMobile) return MOBILE;
    if (isBrowser) return DESKTOP;
    return "";
};

export const getRandomizedDevice = (): DeviceType => {
    return Math.random() < 0.5 ? MOBILE : DESKTOP;
};

export const getDeviceForContext = (): DeviceInterface => {
    const device = getDevice();
    return {
        key: device,
        name: device,
        operating_system: getOperatingSystem(),
        platform: device,
    };
};

export const getRandomizedDeviceForContext = (): DeviceInterface => {
    const randomizedDevice = getRandomizedDevice();
    return {
        key: randomizedDevice,
        name: randomizedDevice,
        operating_system: getRandomizedOperatingSystem(randomizedDevice),
        platform: randomizedDevice,
    };
};

export const getLocation = (): LocationInterface => {
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const continent = timeZone.split("/")[0];
    const city = timeZone.split("/")[timeZone.split("/").length - 1].replace("_", " ");

    return {
        key: timeZone,
        city: city,
        timeZone: timeZone,
        continent: continent,
    };
};

export const getRandomizedLocation = (): LocationInterface => {
    const timeZone = ALL_TIME_ZONES[Math.floor(Math.random() * ALL_TIME_ZONES.length)];
    const continent = timeZone.split("/")[0];
    const city = timeZone.split("/")[timeZone.split("/").length - 1].replace("_", " ");

    return {
        key: timeZone,
        city: city,
        timeZone: timeZone,
        continent: continent,
    };
};

export const getRandomizedUser = () => {
    const randomizedUser = STARTER_PERSONAS[Math.floor(Math.random() * STARTER_PERSONAS.length)];

    return {
        name: randomizedUser.personaname,
        email: randomizedUser.personaemail,
    };
};

export const getHashEmail = (email: string): string => {
    return CryptoJS.SHA256(email).toString();
};

export const getExistingAudienceKey = (): string => {
    return (
        getCookie(LD_CONTEXT_COOKIE_KEY) &&
        JSON.parse(getCookie(LD_CONTEXT_COOKIE_KEY) || "")?.audience?.key
    );
};
