"use client";

import * as React from "react";
import { RotateCcw } from "lucide-react";
import { useRouter } from "next/router";

import {
	CommandDialog,
	CommandEmpty,
	CommandGroup,
	CommandItem,
	CommandList,
} from "@/components/ui/command";
import { toast } from "../../ui/use-toast";
import ExperimentGenerator from "@/components/generators/experimentation-automation/experimentGeneratorGeneral";
import {
	TOGGLEBANK_CHATBOT_AI_EXPERIMENTATION_KEY,
	TOGGLEBANK_SIGNUP_FLOW_EXPERIMENTATION_KEY,
} from "@/components/generators/experimentation-automation/experimentationConstants";
import GuardedReleaseGenerator from "@/components/generators/guarded-release-generator/guardedReleaseGenerator";
import {
	TOGGLEBANK_DB_GUARDED_RELEASE_LDFLAG_KEY,
	TOGGLEBANK_API_GUARDED_RELEASE_LDFLAG_KEY,
	AI_CONFIG_TOGGLEBOT_LDFLAG_KEY,
	RELEASE_NEW_SIGNUP_PROMO_LDFLAG_KEY,
} from "@/utils/flagConstants";

function useQuickCommandDialog() {
	const [open, setOpen] = React.useState(false);
	return { open, setOpen };
}

function QuickCommandDialog({ children }: { children: React.ReactNode }) {
	const { open, setOpen } = useQuickCommandDialog();
	const location = useRouter();
	const [timer, setTimer] = React.useState(0);
	const [showTooltip, setShowTooltip] = React.useState(false);
	const [showScrollIcon, setShowScrollIcon] = React.useState(false);
	const commandListRef = React.useRef(null);

	React.useEffect(() => {
		const down = (e: KeyboardEvent) => {
			if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
				e.preventDefault();
				setOpen((open) => !open);
			}
		};

		document.addEventListener("keydown", down);
		return () => document.removeEventListener("keydown", down);
	}, []);

	React.useEffect(() => {
		const checkOverflow = () => {
			if (commandListRef.current) {
				const { scrollHeight, clientHeight } = commandListRef.current;
				setShowScrollIcon(scrollHeight > clientHeight);
			}
		};

		checkOverflow();
		window.addEventListener("resize", checkOverflow);
		return () => window.removeEventListener("resize", checkOverflow);
	}, [open]);

	const resetFeatureFlags = async () => {
		toast({
			title: "Resetting",
			description:
				"Currently resetting all LaunchDarkly flags for this environment. Give us 30 seconds.",
		});

		setTimer(30);
		const intervalId = setInterval(() => {
			setTimer((prevTimer) => {
				if (prevTimer <= 1) {
					clearInterval(intervalId);
					return 0;
				}
				return prevTimer - 1;
			});
		}, 1000);

		await fetch("/api/ldreset");
		location.reload();
		location.push("/");
	};

	return (
		<>
			{children}
			<CommandDialog open={open} onOpenChange={setOpen}>
				<CommandList className="!max-h-[100rem] h-full">
					<CommandEmpty>No results found.</CommandEmpty>
					<CommandGroup heading="Demo Tools">
						<CommandItem className="cursor-pointer">
							<RotateCcw className="mr-2 h-4 w-4" />
							{timer > 0 ? (
								<p>Resetting in {timer}</p>
							) : (
								<div
									onClick={resetFeatureFlags}
									onMouseEnter={() => setShowTooltip(true)}
									onMouseLeave={() => setShowTooltip(false)}
								>
									<p className="font-bold font-sohnelight text-lg">
										Reset Feature Flags
									</p>
									{showTooltip && (
										<div className="text-lg">
											This tool resets all Feature Flags to the source
											environment's values. To use it, navigate to your LD
											project and open the template environment. Set your
											desired Feature Flag values and targeting options there.
											This tool will then use the template environment as a
											blueprint to apply these settings to your LD environment.
											This process takes 30 seconds to complete
										</div>
									)}
								</div>
							)}
						</CommandItem>
						<CommandItem className="!cursor-pointer">
							<GuardedReleaseGenerator
								flagKey={TOGGLEBANK_API_GUARDED_RELEASE_LDFLAG_KEY}
								title={"[ToggleBank] API Guarded Release Generator (Rollback)"}
							/>
						</CommandItem>
						<CommandItem className="!cursor-pointer">
							<GuardedReleaseGenerator
								flagKey={TOGGLEBANK_DB_GUARDED_RELEASE_LDFLAG_KEY}
								title={
									"[ToggleBank] Database Guarded Release Generator (No Rollback)"
								}
							/>
						</CommandItem>
						<CommandItem className="!cursor-pointer">
							<ExperimentGenerator
								title={
									"[ToggleBank] Feature Experiment Results Generator for AI Chatbot"
								}
								flagKey={AI_CONFIG_TOGGLEBOT_LDFLAG_KEY}
							/>
						</CommandItem>
						<CommandItem className="!cursor-pointer">
							<ExperimentGenerator
								title={
									"[ToggleBank] Funnel Experiment Results Generator for Sign Up Flow"
								}
								flagKey={RELEASE_NEW_SIGNUP_PROMO_LDFLAG_KEY}
							/>
						</CommandItem>
					</CommandGroup>
				</CommandList>
			</CommandDialog>
		</>
	);
}

export { QuickCommandDialog, useQuickCommandDialog };
