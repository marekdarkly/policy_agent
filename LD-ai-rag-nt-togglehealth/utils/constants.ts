import { getCompanyLogos, type Industry } from "./assetLoader";
import architectureIconCSNAV from "@/public/sidenav/architecture-icon.svg";
import architectureHoverCSNAV from "@/public/sidenav/card-demo-sidenav-architecture-hover.svg";
import architectureNoHoverCSNAV from "@/public/sidenav/card-demo-sidenav-architecture.svg";
import codeexamplesHoverCSNAV from "@/public/sidenav/card-demo-sidenav-codeexamples-hover.svg";
import codeexamplesNoHoverCSNAV from "@/public/sidenav/card-demo-sidenav-codeexamples.svg";
import curlyBrackets from "@/public/sidenav/curly-brackets.svg";
import { AIModelInterface, UserDataType } from "./typescriptTypesInterfaceIndustry";
import { Persona } from "@/utils/typescriptTypesInterfaceLogin";

export const ALERT_TYPES = {
    SUCCESS: "success",
    ERROR: "error",
    WARNING: "warning",
    INFO: "info",
};

export const PERSONA_TIER_STANARD = "Standard";
export const PERSONA_TIER_PLATINUM = "Platinum";
export const PERSONA_ROLE_BETA = "Beta";
export const PERSONA_ROLE_DEVELOPER = "Developer";
export const PERSONA_ROLE_USER = "User";
export const LAUNCH_CLUB_STANDARD = "standard";
export const LAUNCH_CLUB_PLATINUM = "platinum";
export const LD_CONTEXT_COOKIE_KEY = "ld-context";

export const BANK = "bank";
export const HEALTH = "health";
export const MENTAL_HEALTH = "mental-health";

export const ANTHROPIC = "anthropic";
export const COHERE = "cohere";
export const META = "meta";
export const ANTHROPIC_CLAUDE = "Anthropic Claude";
export const COHERE_CORAL = "Cohere Command";

export const MOBILE = "Mobile";
export const DESKTOP = "Desktop";
export const ANDROID = "Android";
export const IOS = "iOS";
export const WINDOWS = "Windows";
export const MACOS = "macOS";

export const COMPANY_LOGOS = {
    bank: getCompanyLogos('banking'),
    health: getCompanyLogos('health'),
    mentalHealth: getCompanyLogos('mental-health'),
};

export const DEFAULT_AI_MODEL: AIModelInterface = {
    messages: [
        {
            content:
                "As an AI bot for a travel airline LaunchAirways your purpose is to answer questions related to flights and traveling. Act as customer representative. Only answer queries related to traveling and airlines. Remove quotation in response. Limit response to 100 characters. Here is the user prompt: ${userInput}.",
            role: "system",
        },
    ],
    model: {
        parameters: { temperature: 0.5, maxTokens: 500 },
        name: "cohere.command-text-v14",
    },
    _ldMeta: {
        enabled: true,
        variationKey: "cohere-coral",
        version: 1,
        versionKey: "cohere-coral",
    },
};

export const CSNAV_ITEMS = [
    {
        hoverBackground: codeexamplesHoverCSNAV,
        noHoverBackground: codeexamplesNoHoverCSNAV,
        icon: curlyBrackets,
        type: "resource",
        link: "/examples",
        title: "Code Examples",
    },
    {
        icon: architectureIconCSNAV,
        hoverBackground: architectureHoverCSNAV,
        noHoverBackground: architectureNoHoverCSNAV,
        type: "resource",
        link: "/architecture",
        title: "Architecture",
    },
];

export const NAV_ELEMENTS_VARIANT = {
    bank: {
        navLinks: [
            {
                text: "Summary",
                href: "/",
            },
            // { text: "Transfers", href: "/" },
            { text: "Trades", href: "/" },
            // { text: "External Accounts", href: "/" },
            { text: "Reports", href: "/" },
        ],
        navLinkColor: "gradient-bank",
        popoverMessage: "Thank you for investing with us, ",
        logoImg: COMPANY_LOGOS["bank"].horizontal,
    },
    health: {
        navLinks: [
            {
                text: "Overview",
                href: "/health",
            },
            { text: "Prescriptions", href: "/health" },
            { text: "Appointments", href: "/health" },
            { text: "Records", href: "/health" },
        ],
        navLinkColor: "gradient-health",
        popoverMessage: "Thank you for choosing ToggleHealth, ",
        logoImg: COMPANY_LOGOS["health"].horizontal,
    },
    'mental-health': {
        navLinks: [
            {
                text: "Crisis Monitoring",
                href: "/mental-health",
            },
            { text: "Therapy", href: "/mental-health" },
            { text: "Medication", href: "/mental-health" },
            { text: "Resources", href: "/mental-health" },
        ],
        		navLinkColor: "transparent",
        popoverMessage: "Thank you for choosing Toggle Mental Health, ",
        logoImg: COMPANY_LOGOS["mentalHealth"].horizontal,
    },
};

export const STARTER_PERSONAS: Persona[] = [
    {
        personaname: "Christine",
        personatier: PERSONA_TIER_STANARD,
        personaimage: "/personas/persona3.png",
        personaemail: "user@launchmail.io",
        personarole: PERSONA_ROLE_USER,
    },
    {
        personaname: "Angela",
        personatier: PERSONA_TIER_PLATINUM,
        personaimage: "/personas/persona6.jpg",
        personaemail: "angela@launchmail.io",
        personarole: PERSONA_ROLE_USER,
    },
    {
        personaname: "Alysha",
        personatier: PERSONA_TIER_STANARD,
        personaimage: "personas/beta.png",
        personaemail: "alysha@launchmail.io",
        personarole: PERSONA_ROLE_BETA,
    },
    {
        personaname: "Jenn",
        personatier: PERSONA_TIER_STANARD,
        personaimage: "personas/woman.png",
        personaemail: "jenn@launchmail.io",
        personarole: PERSONA_ROLE_DEVELOPER,
    },
    {
        personaname: "Cody",
        personatier: PERSONA_TIER_STANARD,
        personaimage: "personas/standard.jpg",
        personaemail: "cody@launchmail.io",
        personarole: PERSONA_ROLE_USER,
    },
];


export const INITIAL_USER_SIGNUP_DATA: UserDataType = {
  email: STARTER_PERSONAS[0].personaemail,
  password: "defaultPassword",
  firstName: STARTER_PERSONAS[0].personaname,
  lastName: "Wilson",
  dob: "2/28/1998",
  ssn: "***-**-****",
  phone: "220-415-9634",
  address: "390 Fort St",
  apt: "245",
  zip: "94572",
  selectedServices: ["Telemedicine"],
}