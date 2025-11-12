import { useEffect } from 'react';
import { useLDClient } from "@/utils/industryHook";
import { initializeTelemetry, SessionReplay } from "@launchdarkly/browser-telemetry";

const TelemetryWrapper = ({ children }: { children: React.ReactNode }) => {
  const ldClient = useLDClient();

  useEffect(() => {
    const session = new SessionReplay();
    const telemetry = initializeTelemetry({collectors: [session]});

    if (ldClient && telemetry) {
      telemetry.register(ldClient);
    }
  }, [ldClient]);

  return <>{children}</>;
};

export default TelemetryWrapper;