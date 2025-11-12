import { useState, ReactElement } from "react";
import { CheckingAccount } from "@/components/ui/bankcomponents/checkingview";
import { CreditAccount } from "@/components/ui/bankcomponents/creditview";
import { MorgtgageAccount } from "@/components/ui/bankcomponents/mortgageview";
import { useFlags } from "@/utils/industryHook";
import { oldCheckingData } from "../../../lib/oldCheckingData";
import WealthManagementSheet from "@/components/ui/bankcomponents/wealthManagement";
import { WealthManagementGraph } from "@/components/ui/bankcomponents/WealthManagementGraph";
import Image from "next/image";
import { motion } from "framer-motion";
import { WealthManagementGraphDataType } from "@/utils/typescriptTypesInterfaceIndustry";
import { FederatedCheckingAccount } from "@/components/ui/bankcomponents/federatedChecking";
import { FederatedCreditAccount } from "@/components/ui/bankcomponents/federatedCredit";
import WrapperMain from "../WrapperMain";
import DynamicNav from "../NavComponent/DynamicNav";

import bankDashboardBackgroundLeft from "@/public/investment/backgrounds/investment-dashboard-background-left.svg";
import bankDashboardBackgroundRight from "@/public/investment/backgrounds/investment-dashboard-background-right.svg";

export default function BankUserDashboard() {
	const [loading, setLoading] = useState<boolean>(false);
	const [aiResponse, setAIResponse] = useState<string>("");
	const { wealthManagement, federatedAccounts } = useFlags();
	const money = JSON.stringify(oldCheckingData);
	const prompt: string = `Playing the role of a financial analyst, using the data contained within this information set: ${money}, write me 50 word of an analysis of the data and highlight the item I spend most on. Skip any unnecessary explanations. Summarize the mostly costly area im spending at. Your response should be tuned to talking directly to the requestor.`;
	const viewPrompt: string =
		"Playing the role of a financial analyst, write me 50 word of an analysis of the data and highlight the item I spend most on. Skip any unnecessary explanations. Summarize the mostly costly area im spending at. Your response should be personalized for the user requesting the information.";

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

	const data: WealthManagementGraphDataType[] = [
		{ month: "05/23", balance: 18427 },
		{ month: "06/23", balance: 25345 },
		{ month: "07/23", balance: 32647 },
		{ month: "08/23", balance: 47954 },
		{ month: "09/23", balance: 64234 },
		{ month: "10/23", balance: 83758 },
	];

	return (
		<>
			<Image
				src={bankDashboardBackgroundRight}
				className="fixed right-0 top-0 bottom-0 min-h-screen"
				alt="Bank Home Page Background"
				priority
				style={{
					maxWidth: "100%",
					width: "auto",
					height: "auto",
				}}
			/>
			<Image
				src={bankDashboardBackgroundLeft}
				className="fixed left-0 bottom-0 m-h-screen"
				alt="Bank Home Page Background"
				priority
				style={{
					maxWidth: "100%",
					width: "auto",
					height: "auto",
				}}
			/>
			<WrapperMain>
				<DynamicNav industry="banking" />

				<section className="w-full mb-8 mt-0 sm:mt-8 ">
					<SectionTitle
						text="Portfolio Management"
						textColor="text-blue-600 font-bold"
					/>

					<div className="flex flex-col sm:flex-row w-full gap-y-8 sm:gap-x-8 h-full">
						<section
							className={`w-full flex flex-col px-6 py-8 xl:p-10 shadow-xl min-h-[400px] bg-white rounded-xl border border-zinc-200 ${
								wealthManagement ? "sm:w-[50%] xl:w-[60%]" : "lg:w-[99.9%]"
							}`}
						>
							<WealthManagementGraph data={data} />
						</section>

						{wealthManagement && (
							<section className="w-full sm:w-[50%] xl:w-[40%]">
								<WealthManagementSheet
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
						<SectionTitle text="Account Summary" textColor="text-blue-600" />

						<CardRowWrapper>
							<>
								<MotionCardWrapper>
									<CheckingAccount />
								</MotionCardWrapper>
								<MotionCardWrapper>
									<CreditAccount />
								</MotionCardWrapper>
								<MotionCardWrapper>
									<MorgtgageAccount />
								</MotionCardWrapper>
							</>
						</CardRowWrapper>
					</section>

					{federatedAccounts && (
						<section className={`w-full h-full xl:w-[40%] `}>
							<SectionTitle
								text="Federated Account Access"
								textColor="text-black"
							/>

							<CardRowWrapper>
								<>
									<MotionCardWrapper>
										<FederatedCheckingAccount />
									</MotionCardWrapper>
									<MotionCardWrapper>
										<FederatedCreditAccount />
									</MotionCardWrapper>
								</>
							</CardRowWrapper>
						</section>
					)}
				</section>

				<section className="flex flex-col lg:flex-row w-full h-full gap-y-8 sm:gap-x-8 justify-between">
					<div className="w-full lg:w-1/2">
						<img
							src="banking/SpecialOffer-CC.svg"
							className="shadow-xl rounded-xl w-full"
						/>
					</div>
					<div className="w-full lg:w-1/2 flex justify-end ">
						<img
							src="banking/SpecialOffer-CarLoan.svg"
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
