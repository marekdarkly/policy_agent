import { useState, ReactElement } from "react";
import { CrisisMonitoringAccount } from "@/components/ui/mentalhealthcomponents/crisisview";
import { TherapyAccount } from "@/components/ui/mentalhealthcomponents/therapyview";
import { MedicationAccount } from "@/components/ui/mentalhealthcomponents/medicationview";
import { useFlags } from "@/utils/industryHook";
import WellnessManagementSheet from "@/components/ui/mentalhealthcomponents/wellnessManagement";
import { WellnessManagementGraph } from "@/components/ui/mentalhealthcomponents/WellnessManagementGraph";
import Image from "next/image";
import { motion } from "framer-motion";
import { WellnessManagementGraphDataType } from "@/utils/typescriptTypesInterfaceIndustry";
import { FederatedCrisisAccount } from "@/components/ui/mentalhealthcomponents/federatedCrisis";
import { FederatedTherapyAccount } from "@/components/ui/mentalhealthcomponents/federatedTherapy";
import WrapperMain from "../WrapperMain";
import DynamicNav from "../NavComponent/DynamicNav";

import mentalHealthDashboardBackgroundLeft from "@/public/mental-health/backgrounds/mental-health-dashboard-background-left.svg";
import mentalHealthDashboardBackgroundRight from "@/public/mental-health/backgrounds/mental-health-dashboard-background-right.svg";

export default function MentalHealthUserDashboard() {
	const [loading, setLoading] = useState<boolean>(false);
	const [aiResponse, setAIResponse] = useState<string>("");
	const { wellnessManagement, federatedAccounts } = useFlags();
	const mentalHealthData = JSON.stringify({
		crisisInterventions: 3,
		therapySessions: 12,
		medicationAdherence: 95,
		wellnessScore: 78,
		supportGroupAttendance: 8,
		emergencyContacts: 2
	});
	const prompt: string = `Playing the role of a mental health analyst, using the data contained within this information set: ${mentalHealthData}, write me 50 words of an analysis of the data and highlight the mental health service I use most. Skip any unnecessary explanations. Summarize the most frequently used mental health service. Your response should be tuned to talking directly to the requestor.`;
	const viewPrompt: string =
		"Playing the role of a mental health analyst, write me 50 words of an analysis of the data and highlight the mental health service I use most. Skip any unnecessary explanations. Summarize the most frequently used mental health service. Your response should be personalized for the user requesting the information.";

	async function submitQuery(query: any) {
		try {
			setLoading(true);
			const response = await fetch("/api/bedrock", {
				method: "POST",
				body: JSON.stringify({ prompt: prompt }),
			});

			if (!response.ok) {
				throw new Error(
					`HTTP error! status: ${response.status}. Check API Server Logs.`
				);
			}

			const data = await response.json();
			setAIResponse(data.completion);

			return data.completion;
		} catch (error) {
			console.error("An error occurred:", error);
		} finally {
			setLoading(false);
		}
	}

	const data: WellnessManagementGraphDataType[] = [
		{ month: "05/23", wellnessScore: 65 },
		{ month: "06/23", wellnessScore: 72 },
		{ month: "07/23", wellnessScore: 68 },
		{ month: "08/23", wellnessScore: 75 },
		{ month: "09/23", wellnessScore: 78 },
		{ month: "10/23", wellnessScore: 82 },
	];

	return (
		<>
			<Image
				src={mentalHealthDashboardBackgroundRight}
				className="fixed right-0 top-0 bottom-0 min-h-screen"
				alt="Mental Health Dashboard Background"
				priority
				style={{
					maxWidth: "100%",
					width: "auto",
					height: "auto",
				}}
			/>
			<Image
				src={mentalHealthDashboardBackgroundLeft}
				className="fixed left-0 bottom-0 m-h-screen"
				alt="Mental Health Dashboard Background"
				priority
				style={{
					maxWidth: "100%",
					width: "auto",
					height: "auto",
				}}
			/>
					<WrapperMain>
			<DynamicNav industry="mental-health" />

				<section className="w-full mb-8 mt-0 sm:mt-8 ">
					<SectionTitle
						text="Mental Wellness Management"
						textColor="text-purple-600 font-bold"
					/>

					<div className="flex flex-col sm:flex-row w-full gap-y-8 sm:gap-x-8 h-full">
						<section
							className={`w-full flex flex-col px-6 py-8 xl:p-10 shadow-xl min-h-[400px] bg-white rounded-xl border border-zinc-200 ${
								wellnessManagement ? "sm:w-[50%] xl:w-[60%]" : "lg:w-[99.9%]"
							}`}
						>
							<div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
								<h2 className="text-2xl font-bold text-gray-800 mb-4 sm:mb-0">
									Mental Wellness Overview
								</h2>
								<WellnessManagementSheet
									onSubmit={submitQuery}
									loading={loading}
									aiResponse={aiResponse}
									viewPrompt={viewPrompt}
								/>
							</div>

							<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
								<CrisisMonitoringAccount />
								<TherapyAccount />
								<MedicationAccount />
							</div>

							<div className="flex flex-col sm:flex-row gap-6">
								{federatedAccounts && (
									<>
										<FederatedCrisisAccount />
										<FederatedTherapyAccount />
									</>
								)}
							</div>
						</section>

						{wellnessManagement && (
							<section className="w-full sm:w-[50%] xl:w-[40%] flex flex-col px-6 py-8 xl:p-10 shadow-xl min-h-[400px] bg-white rounded-xl border border-zinc-200">
								<h2 className="text-2xl font-bold text-gray-800 mb-6">
									Mental Wellness Trends
								</h2>
								<WellnessManagementGraph data={data} />
							</section>
						)}
					</div>
				</section>
			</WrapperMain>
		</>
	);
}

interface SectionTitleProps {
	text: string;
	textColor: string;
}

const SectionTitle: React.FC<SectionTitleProps> = ({ text, textColor }) => {
	return (
		<div className="flex items-center justify-between mb-6">
			<h1 className={`text-3xl sm:text-4xl font-audimat ${textColor}`}>
				{text}
			</h1>
		</div>
	);
};
