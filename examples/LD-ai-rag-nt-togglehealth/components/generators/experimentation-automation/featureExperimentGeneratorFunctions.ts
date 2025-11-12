import { COHERE, ANTHROPIC } from "@/utils/constants";
import { wait } from "@/utils/utils";
import { useLDClient } from "@/utils/industryHook";
import {
	AI_CHATBOT_BAD_SERVICE,
	AI_CHATBOT_GOOD_SERVICE,
	BAYESIAN,
	FREQUENTIST,
	experimentTypeIterations,
} from "./experimentationConstants";
import { AI_CONFIG_TOGGLEBOT_LDFLAG_KEY } from "@/utils/flagConstants";

const probablityExperimentTypeAI = {
	[BAYESIAN]: { [ANTHROPIC]: 50, [COHERE]: 80 },
	[FREQUENTIST]: { [ANTHROPIC]: 50, [COHERE]: 58 },
};

export const generateAIChatBotFeatureExperimentResults = async ({
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

	const aiModelVariation = await client?.variation(
		AI_CONFIG_TOGGLEBOT_LDFLAG_KEY,
		{}
	);

	for (let i = 1; i <= totalIterations; i++) {
		if (stopRef.current) {
			setIsComplete(true);
			setIsGenerating(false);
			break;
		}

		if (aiModelVariation._ldMeta.enabled) {
			if (aiModelVariation.model.name.includes(ANTHROPIC)) {
				let probablity = Math.random() * 100;
				if (
					probablity <
					probablityExperimentTypeAI[
						experimentType as keyof typeof probablityExperimentTypeAI
					][ANTHROPIC]
				) {
					await client?.track(AI_CHATBOT_GOOD_SERVICE);
					await client?.flush();
				} else {
					await client?.track(AI_CHATBOT_BAD_SERVICE);
					await client?.flush();
				}
			} else {
				//cohere
				let probablity = Math.random() * 100;
				if (
					probablity <
					probablityExperimentTypeAI[
						experimentType as keyof typeof probablityExperimentTypeAI
					][COHERE]
				) {
					await client?.track(AI_CHATBOT_GOOD_SERVICE);
					await client?.flush();
				} else {
					await client?.track(AI_CHATBOT_BAD_SERVICE);
					await client?.flush();
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
