import { wait } from "@/utils/utils";
import {
	SIGN_UP_STARTED,
	INITIAL_SIGN_UP_COMPLETED,
	SIGN_UP_PERSONAL_DETAIL_COMPLETED,
	SIGNUP_COMPLETED,
	BAYESIAN,
	FREQUENTIST,
	experimentTypeIterations,
} from "./experimentationConstants";
import { useLDClient } from "@/utils/industryHook";
import { RELEASE_NEW_SIGNUP_PROMO_LDFLAG_KEY } from "@/utils/flagConstants";

const NO_BANNER = "No Banner";
const NEW_BANNER = "New Banner";

const probablityExperimentTypeStoreHeader = {
	[BAYESIAN]: {
		[NO_BANNER]: {
			//control
			metric1: 60,
			metric2: 50,
			metric3: 40,
			metric4: 30,
		},
		[NEW_BANNER]: {
			// winner
			metric1: 70,
			metric2: 60,
			metric3: 50,
			metric4: 40,
		},
	},
	[FREQUENTIST]: {
		[NO_BANNER]: {
			//control
			metric1: 66,
			metric2: 56,
			metric3: 46,
			metric4: 36,
		},
		[NEW_BANNER]: {
			// winner
			metric1: 70,
			metric2: 60,
			metric3: 50,
			metric4: 40,
		},
	},
};

export const generateSignUpFlowFunnelExperimentResults = async ({
	client,
	updateContext,
	setProgress,
	setIsGenerating,
	setIsComplete,
	experimentType,
	setCurrentIteration,
	stopRef,
	setIsStopped
}: {
	client: LDClient | undefined;
	updateContext: () => void;
	setProgress: React.Dispatch<React.SetStateAction<number>>;
	setIsGenerating: React.Dispatch<React.SetStateAction<boolean>>;
	setIsComplete: React.Dispatch<React.SetStateAction<boolean>>;
	experimentType: string;
	setCurrentIteration: React.Dispatch<React.SetStateAction<number>>;
	stopRef: React.MutableRefObject<any>;
	setIsStopped: React.Dispatch<React.SetStateAction<boolean>>;
}): Promise<void> => {
	setCurrentIteration(0);
	setProgress(0);
	setIsComplete(false);
	setIsGenerating(true);
	setIsStopped(false);
	stopRef.current = false

	const totalIterations =
		experimentTypeIterations[
			experimentType as keyof typeof experimentTypeIterations
		];

	const flagVariation: string = client?.variation(
		RELEASE_NEW_SIGNUP_PROMO_LDFLAG_KEY,
		false
	);

	//if true then control else winner
	let variationName = "";
	if (flagVariation) {
		variationName = NEW_BANNER;
	} else {
		variationName = NO_BANNER;
	}

	const metricProbablityObj =
		probablityExperimentTypeStoreHeader[
			experimentType as keyof typeof probablityExperimentTypeStoreHeader
		];

	const metricProbablity =
		metricProbablityObj[variationName as keyof typeof metricProbablityObj];

	for (let i = 1; i <= totalIterations; i++) {
		if (stopRef.current) {
			setIsComplete(true);
			setIsGenerating(false);
			break;
		}
		const stage1metric = Math.random() * 100;

		if (stage1metric < metricProbablity.metric1) {
			await client?.track(SIGN_UP_STARTED);
			await client?.flush();
			const stage2metric = Math.random() * 100;

			if (stage2metric < metricProbablity.metric2) {
				await client?.track(INITIAL_SIGN_UP_COMPLETED);
				await client?.flush();
				const stage3metric = Math.random() * 100;

				if (stage3metric < metricProbablity.metric3) {
					await client?.track(SIGN_UP_PERSONAL_DETAIL_COMPLETED);
					await client?.flush();
					const stage4metric = Math.random() * 100;

					if (stage4metric < metricProbablity.metric4) {
						await client?.track(SIGNUP_COMPLETED);
						await client?.flush();
					}
				}
			}
		}
		setCurrentIteration(i);
		setProgress(
			(prevProgress: number) => prevProgress + (1 / totalIterations) * 100
		);
		await wait(0.25);

		await client?.flush();
		await updateContext();

		// If this is the last iteration, mark as complete
		if (i === totalIterations) {
			setIsComplete(true);
			setIsGenerating(false);
		}
	}
};
