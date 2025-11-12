import { useState, useEffect, useRef, useContext } from "react";
import { useFlags, useLDClient } from "@/utils/industryHook";
import { randomLatency } from "@/utils/utils";
import LoginContext from "@/utils/contexts/login";
import { Beaker } from "lucide-react";
import { TOGGLEBANK_API_GUARDED_RELEASE_LDFLAG_KEY, TOGGLEBANK_DB_GUARDED_RELEASE_LDFLAG_KEY } from "@/utils/flagConstants";
import { STOCK_API_ERROR_RATES, RECENT_TRADES_DB_ERRORS,RECENT_TRADES_DB_LATENCY, STOCK_API_LATENCY } from "../experimentation-automation/experimentationConstants";


const GuardedReleaseGenerator = ({ flagKey, title }:{flagKey: string, title:string}) => {
	const {  updateRandomizedUserContext } = useContext(LoginContext);
	const releaseFlag = useFlags()[flagKey];
	const ldClient = useLDClient();
	const [trueCounter, setTrueCounter] = useState(0);

	useEffect(() => {
		if (releaseFlag) {
			setTrueCounter((prevCounter) => prevCounter + 1);
		}
	}, [releaseFlag]);

	const [runDemo, setRunDemo] = useState(false);
	const [elapsedTime, setElapsedTime] = useState(0);

	const elapsedTimeRef = useRef(elapsedTime);

	useEffect(() => {
		elapsedTimeRef.current = elapsedTime;
	}, [elapsedTime]);

	useEffect(() => {

		let loginInterval: NodeJS.Timeout | null = null;
		let errorInterval: NodeJS.Timeout | null = null;

		if (runDemo) {
			loginInterval = setInterval(() => {
				setElapsedTime((prevTime) => {
					const newTime = prevTime + 1;
					if (newTime % 1 === 0) {
						updateRandomizedUserContext();
					}
					return newTime;
				});
			}, 100);

			errorInterval = setInterval(async () => {
				if (ldClient) {
					if (releaseFlag) {
						// Simulate metrics for the release flag being enabled
						await simulateMetrics(ldClient, true);
					} else {
						// Simulate metrics for the release flag being disabled
						await simulateMetrics(ldClient, false);
					}
				}
				setElapsedTime((prevTime) => prevTime + 1);
			}, 50);
		}

		return () => {
			if (runDemo) {
				if (loginInterval !== null) clearInterval(loginInterval);
				if (errorInterval !== null) clearInterval(errorInterval);
			}
		};
	}, [ldClient, releaseFlag, runDemo]);

	const simulateMetrics = async (client: LDClient, isEnabled: boolean) => {
		let latency = 0;
		let errorRate = 0; 
		let errorMetric = "";
		let latencyMetric = "";

		if(flagKey === TOGGLEBANK_API_GUARDED_RELEASE_LDFLAG_KEY){
			errorMetric = STOCK_API_ERROR_RATES;
			latencyMetric = STOCK_API_LATENCY;
			latency = isEnabled ? randomLatency(500, 600) : randomLatency(40, 50);
			errorRate = isEnabled ? 75 : 25;
		}
		if(flagKey === TOGGLEBANK_DB_GUARDED_RELEASE_LDFLAG_KEY){
			errorMetric = RECENT_TRADES_DB_ERRORS;
			latencyMetric = RECENT_TRADES_DB_LATENCY;
			latency = isEnabled ? randomLatency(30, 45) : randomLatency(34, 43);
			errorRate = isEnabled ? 15 : 15;
		}

		client.track(latencyMetric, undefined, latency);

		await client.flush();
		if (Math.random() * 100 < errorRate) {
			client.track(errorMetric);
			await client.flush();
		}
	};

	const toggleRunDemo = () => {
		setRunDemo((prev) => !prev);
	};

	return (
		<div onClick={toggleRunDemo}
			className="flex items-center"
			>
				<Beaker className="mr-2 h-4 w-4" />
			<div
				className="font-bold font-sohnelight text-lg ml-2"

			>
				{title}
			</div>
			{runDemo && (
				<div className="ml-4 flex justify-between w-full">
					<p className="font-medium">Generating Data...</p>
					<p className="text-sm text-gray-600">Users Exposed : {trueCounter}</p>
				</div>
			)}
		</div>
	);
};

export default GuardedReleaseGenerator;
