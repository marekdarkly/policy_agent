import { Dialog, DialogContent, DialogTrigger, DialogTitle } from "@/components/ui/dialog";
import React, { useState, useContext, useRef } from "react";
import LoginContext from "@/utils/contexts/login";
import { useLDClient } from "@/utils/industryHook";
import { generateAIChatBotFeatureExperimentResults } from "@/components/generators/experimentation-automation/featureExperimentGeneratorFunctions";
import { generateSignUpFlowFunnelExperimentResults } from "@/components/generators/experimentation-automation/funnelExperimentGeneratorFunctions";
import { Beaker, FlaskConical } from "lucide-react";
import { useLDClientError } from "@/utils/industryHook";
import { capitalizeFirstLetter } from "@/utils/utils";
import { BAYESIAN, FREQUENTIST } from "./experimentationConstants";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ExperimentGenerator({
	title,
	flagKey,
}: {
	title: string;
	flagKey: string;
}) {
	const client = useLDClient();
	const { updateRandomizedUserContext } = useContext(LoginContext);
	const [isGenerating, setIsGenerating] = useState(false);
	const [isComplete, setIsComplete] = useState(false);
	const [progress, setProgress] = useState<number>(0);
	const [currentIteration, setCurrentIteration] = useState(0);
	const [experimentTypeObj, setExperimentTypeObj] = useState<{
		experimentType: string;
		numOfRuns: number;
	}>({ experimentType: "", numOfRuns: 0 });
	const ldClientError = useLDClientError();
	const [isStopped, setIsStopped] = useState(false);
	const stopRef = useRef(false);

	if (ldClientError) {
		alert("Error in LaunchDarkly Client");
	}

	const runGenerator = async ({
		flagKey,
		experimentType,
	}: {
		flagKey: string;
		experimentType: string;
	}) => {
		const functionInputs = {
			client: client,
			updateContext: updateRandomizedUserContext,
			setProgress: setProgress,
			setIsGenerating: setIsGenerating,
			setIsComplete: setIsComplete,
			experimentType: experimentType,
			setCurrentIteration: setCurrentIteration,
			stopRef: stopRef,
			setIsStopped: setIsStopped,
		};
		if (flagKey?.includes("signup")) {
			await generateSignUpFlowFunnelExperimentResults({
				...functionInputs,
			});
		} else {
			await generateAIChatBotFeatureExperimentResults({
				...functionInputs,
			});
		}
	};

	const stopGenerator = () => {
		stopRef.current = true;
		setIsStopped(true);
	};

	return (
		<>
			{flagKey?.includes("signup") ? (
				<FlaskConical className="mr-2 h-4 w-4" />
			) : (
				<Beaker className="mr-2 h-4 w-4" />
			)}
			<Dialog>
				<DialogTrigger asChild className="cursor-pointer">
					<p className="font-bold font-sohnelight text-lg">{title}</p>
				</DialogTrigger>
				<DialogContent onCloseAutoFocus={()=>stopGenerator()}>
					<DialogTitle className="sr-only">{title}</DialogTitle>
					<div className="flex flex-col justify-center text-xl font-bold items-center h-full gap-y-4">
						<span className="text-center">{title}</span>
						<div className="flex flex-col gap-x-4 w-full">
							{isGenerating && (
								<div className="">
									<div className="mb-4 font-bold text-lg">
										<span>
											Generating Data{" "}
											{capitalizeFirstLetter(experimentTypeObj.experimentType)}{" "}
											Experimentation
										</span>
									</div>

									<div className="mb-2">
										<div className="flex justify-between mb-2">
											<span className="text-gray-500 text-sm font-normal">
												Progress
											</span>
											<Badge
												variant={
													isComplete
														? "success"
														: isStopped
														? "destructive"
														: "outline"
												}
												className={
													isComplete
														? "bg-green-500 hover:bg-green-600"
														: isStopped
														? "bg-destructive"
														: ""
												}
											>
												{isComplete
													? "Complete"
													: isStopped
													? "Stopped"
													: `${progress.toFixed(2)}%`}
											</Badge>
										</div>
										<Progress value={progress} className="h-2" />
									</div>
									<div className="flex items-center justify-start mb-4">
										<span className="text-gray-500 text-sm font-normal">
											Iterations: {currentIteration}/
											{experimentTypeObj.numOfRuns}
										</span>
									</div>
								</div>
							)}
							<div className="flex gap-x-4 w-full">
								{!isGenerating && (
									<>
										<Button
											onClick={async () => {
												const bayesianExperimentTypeObj = {
													experimentType: "bayesian",
													numOfRuns: 500,
												};
												await setExperimentTypeObj(bayesianExperimentTypeObj);
												runGenerator({ flagKey, experimentType: BAYESIAN });
											}}
											disabled={isGenerating}
											className={` w-full ${"bg-gradient-airways"} h-full p-2 text-lg rounded-sm hover:brightness-125 text-white`}
										>
											Start Bayesian Experiment Generator
										</Button>
										<Button
											onClick={async () => {
												const frequentistExperimentTypeObj = {
													experimentType: "frequentist",
													numOfRuns: 10000,
												};
												await setExperimentTypeObj(
													frequentistExperimentTypeObj
												);
												runGenerator({
													flagKey,
													experimentType: FREQUENTIST,
												});
											}}
											disabled={isGenerating}
											className={` w-full ${"bg-gradient-experimentation"} h-full p-2 text-lg rounded-sm hover:brightness-125 text-white`}
										>
											Start Frequentist Experiment Generator
										</Button>
									</>
								)}
								{isGenerating && (
									<>
										<Button
											onClick={stopGenerator}
											variant="destructive"
											className="w-1/2"
										>
											Stop
										</Button>
										<Button disabled={isGenerating} className="w-full">
											{isGenerating && (
												<>
													<Loader2 className="mr-2 h-4 w-4 animate-spin" />
													Generating...
												</>
											)}
										</Button>
									</>
								)}
							</div>
						</div>
					</div>
				</DialogContent>
			</Dialog>
		</>
	);
}
