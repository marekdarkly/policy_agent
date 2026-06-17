import { useSyncExternalStore } from "react";

/**
 * Demo "fake login" users for the ToggleBank UI.
 *
 * Each preset drives LaunchDarkly user-key targeting so the same AI Configs
 * can resolve to different variations depending on who is "logged in":
 *   - commercial  -> user_key "marek-commercial-plan" (a regular banking customer)
 *   - internal    -> user_key "marek-internal-dev"    (an internal/employee user)
 *
 * The fields below are forwarded to POST /api/chat and become the LaunchDarkly
 * context attributes (see backend create_user_profile). `domain: "togglebank"`
 * keeps the context coherent with the banking brand.
 */
export const DEMO_USERS = {
  commercial: {
    id: "commercial",
    name: "Marek Poliks",
    badge: "Customer",
    userName: "Marek Poliks",
    userKey: "marek-commercial-plan",
    userType: "customer",
    role: "customer",
    plan: "commercial",
    domain: "togglebank",
    policyId: "ACC-90021",
    coverageType: "Everyday Current Account",
  },
  internal: {
    id: "internal",
    name: "Dev Mode",
    badge: "Internal",
    userName: "Marek Poliks",
    userKey: "marek-internal-dev",
    userType: "internal",
    role: "employee",
    plan: "internal",
    domain: "togglebank",
    policyId: "ACC-INT-001",
    coverageType: "Premier Current Account",
  },
} as const;

export type DemoUserId = keyof typeof DEMO_USERS;
export type DemoUser = (typeof DEMO_USERS)[DemoUserId];

// Module-level store so every component that calls useDemoUser() shares the
// same selection and re-renders when it changes — no React context/provider
// required (none is mounted in App.tsx).
let currentId: DemoUserId = "commercial";
const listeners = new Set<() => void>();

const subscribe = (cb: () => void) => {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
};

const getSnapshot = () => currentId;

export function setDemoUser(id: DemoUserId) {
  if (id in DEMO_USERS && id !== currentId) {
    currentId = id;
    listeners.forEach((l) => l());
  }
}

export function useDemoUser() {
  const id = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
  return { user: DEMO_USERS[id], setUser: setDemoUser };
}
