import { createContext, useEffect, useState, useContext } from "react";
import { useFlags, useLDClient } from "@/utils/industryHook";
import Prism from "prismjs";
import LoginContext from "@/utils/contexts/login";
import { ReactNode } from "react";

const LiveLogsContext = createContext<{
	liveLogs: any[];
	currentLDFlagEnvValues: any[];
	logLDMetricSent: ({
		metricKey,
		metricValue,
	}: {
		metricKey: string;
		metricValue?: number;
	}) => void;
	clearLiveLogs: () => void;
}>({
	liveLogs: [],
	currentLDFlagEnvValues: [],
	logLDMetricSent: () => {},
	clearLiveLogs: () => {},
});

export default LiveLogsContext;

export const LiveLogsProvider = ({ children }: { children: ReactNode }) => {
	const [liveLogs, setLiveLogs] = useState<any[]>([]);
	const [currentLDFlagEnvValues, setCurrentLDFlagEnvValues] = useState<
		[string, any][]
	>([]);
	const allLDFlags = useFlags();
	const ldClient = useLDClient();
	const { appMultiContext } = useContext(LoginContext);

	useEffect(() => {
		Prism.highlightAll();
	}, []);

	useEffect(() => {
		setCurrentLDFlagEnvValues(Object.entries(allLDFlags));
	}, [allLDFlags]);

	useEffect(() => {
		ldClient?.on("change", (settings) => {
			const time = new Date();

			setLiveLogs((prevLogs) => {
				return [
					...prevLogs,
					{
						date: time,
						log: JSON.stringify(settings, null, 4),
						type: "New LD Flag Change Event Received",
						color: "text-white bg-airlinedarkblue",
					},
				];
			});
		});
	}, [ldClient]);

	useEffect(() => {
		const time = new Date();

		setLiveLogs((prevLogs) => {
			return [
				...prevLogs,
				{
					date: time,
					log: JSON.stringify(appMultiContext, null, 4),
					type: "New LD Context Change Event Sent",
					color: "text-black bg-gray-200",
				},
			];
		});
	}, [appMultiContext]);

	const logLDMetricSent = ({
		metricKey,
		metricValue,
	}: {
		metricKey: string;
		metricValue?: number;
	}) => {
		const time = new Date();
		setLiveLogs((prevLogs) => {
			return [
				...prevLogs,
				{
					date: time,
					log: `ldClient?.track(${metricKey}, ldClient.getContext() ${
						metricValue && `, ${metricValue}`
					});`,
					type: "New LD Metric Sent",
					color: "text-white bg-purple-500",
				},
			];
		});
	};

	const clearLiveLogs = () => {
		setLiveLogs([]);
	};

	return (
		<LiveLogsContext.Provider
			value={{
				liveLogs,
				currentLDFlagEnvValues,
				logLDMetricSent,
				clearLiveLogs,
			}}
		>
			{children}
		</LiveLogsContext.Provider>
	);
};
