import { useState, ReactElement } from "react";
import { PrescriptionAccount } from "@/components/ui/healthcomponents/prescriptionview";
import { TelemedicineAccount } from "@/components/ui/healthcomponents/telemedicineview";
import { PharmacyAccount } from "@/components/ui/healthcomponents/pharmacyview";
import { useFlags } from "@/utils/industryHook";
import { oldHealthData } from "../../../lib/oldHealthData";
import WellnessManagementSheet from "@/components/ui/healthcomponents/wellnessManagement";
import { WellnessManagementGraph } from "@/components/ui/healthcomponents/WellnessManagementGraph";
import Image from "next/image";
import { motion } from "framer-motion";
import { WellnessManagementGraphDataType } from "@/utils/typescriptTypesInterfaceIndustry";
import { FederatedPrescriptionAccount } from "@/components/ui/healthcomponents/federatedPrescription";
import { FederatedTelemedicineAccount } from "@/components/ui/healthcomponents/federatedTelemedicine";
import WrapperMain from "../WrapperMain";
import DynamicNav from "../NavComponent/DynamicNav";

import healthDashboardBackgroundLeft from "@/public/health/backgrounds/health-dashboard-background-left.svg";
import healthDashboardBackgroundRight from "@/public/health/backgrounds/health-dashboard-background-right.svg";

export default function HealthUserDashboard() {
	const [loading, setLoading] = useState<boolean>(false);
	const [aiResponse, setAIResponse] = useState<string>("");
	const { wellnessManagement, federatedAccounts } = useFlags();
	const healthData = JSON.stringify(oldHealthData);
	const prompt: string = `Playing the role of a health analyst, using the data contained within this information set: ${healthData}, write me 50 words of an analysis of the data and highlight the health service I use most. Skip any unnecessary explanations. Summarize the most frequently used health service. Your response should be tuned to talking directly to the requestor.`;
	const viewPrompt: string =
		"Playing the role of a health analyst, write me 50 words of an analysis of the data and highlight the health service I use most. Skip any unnecessary explanations. Summarize the most frequently used health service. Your response should be personalized for the user requesting the information.";

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
		{ month: "05/23", wellnessScore: 75 },
		{ month: "06/23", wellnessScore: 82 },
		{ month: "07/23", wellnessScore: 78 },
		{ month: "08/23", wellnessScore: 85 },
		{ month: "09/23", wellnessScore: 88 },
		{ month: "10/23", wellnessScore: 92 },
	];

	return (
		<>
			<Image
				src={healthDashboardBackgroundRight}
				className="fixed right-0 top-0 bottom-0 min-h-screen"
				alt="Health Dashboard Background"
				priority
				style={{
					maxWidth: "100%",
					width: "auto",
					height: "auto",
				}}
			/>
			<Image
				src={healthDashboardBackgroundLeft}
				className="fixed left-0 bottom-0 m-h-screen"
				alt="Health Dashboard Background"
				priority
				style={{
					maxWidth: "100%",
					width: "auto",
					height: "auto",
				}}
			/>
			<WrapperMain>
				<DynamicNav industry="health" />

				<section className="w-full mb-8 mt-0 sm:mt-8 ">
					<SectionTitle
						text="Wellness Management"
						textColor="text-green-600 font-bold"
					/>

					<div className="flex flex-col sm:flex-row w-full gap-y-8 sm:gap-x-8 h-full">
						<section
							className={`w-full flex flex-col px-6 py-8 xl:p-10 shadow-xl min-h-[400px] bg-white rounded-xl border border-zinc-200 ${
								wellnessManagement ? "sm:w-[50%] xl:w-[60%]" : "lg:w-[99.9%]"
							}`}
						>
							<WellnessManagementGraph data={data} />
						</section>

						{wellnessManagement && (
							<section className="w-full sm:w-[50%] xl:w-[40%]">
								<WellnessManagementSheet
									data={data}
									aiPrompt={viewPrompt}
									submitQuery={submitQuery}
									prompt={prompt}
									loading={loading}
									aiResponse={aiResponse}
								/>
							</section>
						)}
					</div>
				</section>

				<section
					className={`flex flex-col xl:flex-row mb-8 font-sohne  ${
						federatedAccounts ? "gap-y-8 sm:gap-x-8" : ""
					}`}
				>
					<section
						className={`w-full h-full ${
							federatedAccounts ? "xl:w-[60%]" : "xl:w-full"
						}  `}
					>
						<SectionTitle text="Health Services Summary" textColor="text-green-600" />

						<CardRowWrapper>
							<>
								<MotionCardWrapper>
									<PrescriptionAccount />
								</MotionCardWrapper>
								<MotionCardWrapper>
									<TelemedicineAccount />
								</MotionCardWrapper>
								<MotionCardWrapper>
									<PharmacyAccount />
								</MotionCardWrapper>
							</>
						</CardRowWrapper>
					</section>

					{federatedAccounts && (
						<section className={`w-full h-full xl:w-[40%] `}>
							<SectionTitle
								text="Federated Health Access"
								textColor="text-black"
							/>

							<CardRowWrapper>
								<>
									<MotionCardWrapper>
										<FederatedPrescriptionAccount />
									</MotionCardWrapper>
									<MotionCardWrapper>
										<FederatedTelemedicineAccount />
									</MotionCardWrapper>
								</>
							</CardRowWrapper>
						</section>
					)}
				</section>

				<section className="flex flex-col lg:flex-row w-full h-full gap-y-8 sm:gap-x-8 justify-between">
					<div className="w-full lg:w-1/2">
						<img
							src="health/SpecialOffer-Consultation.svg"
							className="shadow-xl rounded-xl w-full"
						/>
					</div>
					<div className="w-full lg:w-1/2 flex justify-end ">
						<img
							src="health/SpecialOffer-Wellness.svg"
							className="shadow-xl rounded-xl w-full"
						/>
					</div>
				</section>
			</WrapperMain>
		</>
	);
}

const MotionCardWrapper = ({ children }: { children: ReactElement }) => {
	return (
		<motion.div
			className="p-4 h-[300px] w-full flex-1 bg-white shadow-xl rounded-2xl cursor-pointer"
			whileHover={{ scale: 1.1 }}
		>
			{children}
		</motion.div>
	);
};

const CardRowWrapper = ({ children }: { children: ReactElement }) => {
	return (
		<div className="flex flex-col sm:flex-row gap-y-8 sm:gap-x-4">
			{children}
		</div>
	);
};

const SectionTitle = ({
	textColor,
	text,
}: {
	textColor: string;
	text: string;
}) => {
	return <h2 className={` text-2xl mb-6 ${textColor}`}>{text}</h2>;
}; 