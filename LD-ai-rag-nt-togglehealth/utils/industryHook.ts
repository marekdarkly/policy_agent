import { useMemo } from "react";

// Simple hook to get industry value from environment variable
export const useIndustry = () => {
    // Get industry from environment variable, default to "banking"
    const industry = process.env.NEXT_PUBLIC_INDUSTRY || "banking";
    return { industry, loading: false, error: null };
};

// Mock implementations for LaunchDarkly hooks that components are using
export const useFlags = () => {
    const { industry, loading } = useIndustry();
    
    // Use useMemo to ensure stable reference
    return useMemo(() => ({
        "nt-toggle-rag-demo": industry,
        "release-new-signup-promo": false,
        "togglebankAPIGuardedRelease": false,
        "togglebankDBGuardedRelease": false,
        "wellnessManagement": industry === "health" || industry === "mental-health",
        "federatedAccounts": false,
        "wealthManagement": industry === "banking",
        "financialDBMigration": false,
        // Add the AI config flag with the expected structure
        "toggle-rag": {
            _ldMeta: {
                enabled: true
            },
            model: {
                name: "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
            }
        },
    }), [industry]);
};

export const useLDClient = () => {
    // Use useMemo to ensure stable reference
    return useMemo(() => ({
        track: () => {},
        identify: async () => {}, // Async method for context changes
        flush: () => {},
        close: () => {},
        setStreaming: () => {},
        setOffline: () => {},
        setOnline: () => {},
        on: () => {}, // Mock event listener method
        off: () => {}, // Mock event removal method
        getContext: () => ({}), // Mock context getter
        waitForInitialization: async () => {}, // Async method for initialization
    }), []);
};

export const useLDClientError = () => {
    return null; // No error since we're not using client-side LaunchDarkly
};
