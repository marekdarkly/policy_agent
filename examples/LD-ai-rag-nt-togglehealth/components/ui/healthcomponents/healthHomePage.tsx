import { ReactElement, useContext } from "react";
import { useFlags, useLDClient } from "@/utils/industryHook";
import { motion } from "framer-motion";
import Image from "next/image";
import { Button } from "../button";
import { useRouter } from "next/router";
import { StaticImageData } from "next/image";
import WrapperMain from "../WrapperMain";
import DynamicNav from "../NavComponent/DynamicNav";
import LiveLogsContext from "@/utils/contexts/LiveLogsContext";
import { SIGN_UP_STARTED } from "@/components/generators/experimentation-automation/experimentationConstants";

import heroBackgroundPills from "@/public/health/backgrounds/health-hero-background-pills.svg";
import heroBackgroundHeart from "@/public/health/backgrounds/health-hero-background-heart.svg";
import prescriptions from "@/public/health/icons/prescriptions.svg";
import prescriptionsOnHover from "@/public/health/icons/prescriptions-on-hover.svg";
import telemedicine from "@/public/health/icons/telemedicine.svg";
import telemedicineOnHover from "@/public/health/icons/telemedicine-on-hover.svg";
import pharmacy from "@/public/health/icons/pharmacy.svg";
import pharmacyOnHover from "@/public/health/icons/pharmacy-on-hover.svg";
import wellness from "@/public/health/icons/wellness.svg";
import wellnessOnHover from "@/public/health/icons/wellness-on-hover.svg";
import insurance from "@/public/health/icons/insurance.svg";
import insuranceOnHover from "@/public/health/icons/insurance-on-hover.svg";
import healthBackground from "@/public/health/backgrounds/health-homepage-health-card-background.svg";
import specialOfferBackground from "@/public/health/backgrounds/health-homepage-specialoffer-background.svg";
import healthHomePageBackgroundRight from "@/public/health/backgrounds/health-homepage-background-right.svg";
import healthHomePageBackgroundLeft from "@/public/health/backgrounds/health-homepage-background-left.svg";
import { RELEASE_NEW_SIGNUP_PROMO_LDFLAG_KEY } from "@/utils/flagConstants";

export default function HealthHomePage() {
	const router = useRouter();
	const ldClient = useLDClient();
	const { logLDMetricSent } = useContext(LiveLogsContext);
	const releaseNewSignUpPromoLDFlag =
		useFlags()[RELEASE_NEW_SIGNUP_PROMO_LDFLAG_KEY] ??
		healthHomePageValues.industryMessages;

	return (
		<>
			<Image
				src={healthHomePageBackgroundRight}
				className="fixed right-0 bottom-0 min-h-screen"
				alt="Health Home Page Background"
				style={{
					width: "auto",
					height: "auto",
				}}
			/>
			<Image
				src={healthHomePageBackgroundLeft}
				className="fixed left-0 bottom-0 min-h-screen"
				alt="Health Home Page Background"
				style={{
					width: "auto",
					height: "auto",
				}}
			/>
			<WrapperMain className="min-w-full">
				<DynamicNav industry="health" />
				<header className={`w-full relative 3xl:mx-auto 3xl:max-w-7xl`}>
					<Image
						src={heroBackgroundPills}
						className="absolute right-0 w-2/6 xl:w-2/6 min-w-lg max-w-lg opacity-40 sm:opacity-60 xl:opacity-100 z-[-100]"
						alt="Icon Background"
						priority
						style={{
							maxWidth: "100%",
							width: "auto",
							height: "auto",
						}}
					/>
					<Image
						src={heroBackgroundHeart}
						className="absolute left-0 bottom-0 w-2/6 xl:w-2/6 max-w-lg opacity-40 sm:opacity-60 xl:opacity-100 z-[-100]"
						alt="Icon Background"
						priority
						style={{
							maxWidth: "100%",
							width: "auto",
							height: "auto",
						}}
					/>

					<section className="w-full max-w-7xl py-14 sm:py-[8rem] xl:mx-auto flex flex-col sm:flex-row justify-between items-center">
						<div className="flex flex-col text-white w-full sm:w-3/4 xl:w-1/2 justify-start mb-4 pr-0 sm:pr-10 sm:mb-0 gap-y-10 z-10">
							<h1 className="text-5xl sm:text-5xl md:text-6xl lg:text-7xl font-audimat col-span-1 sm:col-span-0 w-full bg-health-gradient-text-color bg-clip-text text-transparent pr-2 sm:pr-6 md:pr-8 lg:pr-10 xl:pr-8">
								Your health, simplified with ToggleHealth
							</h1>
							<p className="text-lg sm:text-md md:text-xl lg:text-xl col-span-2 sm:col-span-0 font-sohnelight w-full text-black pr-6 sm:pr-6 md:pr-8 lg:pr-10 xl:pr-8 ">
								{releaseNewSignUpPromoLDFlag
									? "Sign up today and get your first consultation free!"
									: healthHomePageValues.industryMessages}
							</p>
							<div className="flex space-x-4 pr-6 sm:pr-2 md:pr-4 lg:pr-6 xl:pr-8">
								<Button
									className="shadow-2xl bg-health-gradient-green-background hover:bg-health-gradient-text-color hover:text-white text-white rounded-3xl font-sohnelight w-28 h-10 sm:w-32 sm:h-11 md:w-36 md:h-12 lg:w-40 lg:h-14 xl:w-36 xl:h-12 text-xs sm:text-md md:text-lg lg:text-xl xl:text-xl"
									onClick={() => {
										ldClient?.track(SIGN_UP_STARTED);
										logLDMetricSent({ metricKey: SIGN_UP_STARTED });
										router.push("/signup");
									}}
								>
									Get Started
								</Button>
								<Button className="shadow-2xl border bg-white hover:bg-health-gradient-text-color border-green-800 hover:border-healthhomepagebuttongreen hover:text-white text-green-800  rounded-3xl font-sohnelight w-28 h-10 sm:w-32 sm:h-11 md:w-36 md:h-12 lg:w-40 lg:h-14 xl:w-36 xl:h-12 text-xs sm:text-md md:text-lg lg:text-xl xl:text-xl">
									Learn More
								</Button>
							</div>
						</div>
					</section>
				</header>
				<section className="2xl:mt-20 mx-auto max-w-7xl">
					<h2 className="flex justify-center text-healthhomepagebuttongreen font-sohne tracking-widest text-md sm:text-xl 2xl:text-2xl">
						OUR HEALTH SERVICES
					</h2>

					<section
						className="w-full xl:w-3/4 grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 font-sohnelight text-center  mx-auto gap-y-8 
            xl:gap-y-0 gap-x-8
          sm:gap-x-12 xl:gap-x-24 py-8"
					>
						{healthHomePageValues?.healthServicesArr.map(
							(ele: { imgSrc: StaticImageData; title: string }, i: number) => {
								return (
									<motion.div
										className="flex flex-col items-center"
										key={i}
										whileHover={{ scale: 1.2 }}
									>
										<div className="relative w-24 h-24  cursor-pointer  bg-white rounded-full shadow-2xl sm:shadow-none flex items-center justify-center">
											<Image
												src={ele?.imgSrc}
												className=""
												alt={ele?.title}
												priority
												style={{
													maxWidth: "100%",
													width: "auto",
													height: "auto",
												}}
											/>
										</div>
										<p className="text-xl mt-2 font-sohnelight">{ele?.title}</p>
									</motion.div>
								);
							}
						)}
					</section>
				</section>
				<section className="w-full xl:w-3/4 mx-auto my-10 max-w-7xl flex flex-col gap-y-10">
					<AdContentRowWrapper
						leftChild={
							<div className="bg-health-gradient-green-background p-4 rounded-2xl h-full">
								<AdContentCard
									title={"TELEMEDICINE"}
									subtitle="Virtual care at your fingertips"
									contentText="Connect with healthcare providers from the comfort of your home, anytime, anywhere."
								/>
							</div>
						}
						rightChild={
							<div className="bg-white p-4 rounded-2xl flex h-full">
								<div className="flex flex-col gap-y-6 mt-4 w-full sm:w-1/2">
									<div className="mx-8 text-sm text-gray-400 tracking-widest font-sohnelight">
										WELLNESS PROGRAMS
									</div>
									<div className="mx-8 mt-4 text-green-600 font-sohne text-xl">
										Preventive care & wellness
									</div>
									<div className="text-black mx-8 mb-4 font-sohne text-md">
										Join our wellness programs designed to keep you healthy and active.
									</div>
								</div>
								<div className="w-1/2 items-center justify-center hidden sm:flex">
									<Image
										src={healthBackground}
										width={200}
										height={50}
										alt="Health Background"
										priority
										style={{
											width: "auto",
											maxWidth: "100%",
											height: "auto",
										}}
									/>
								</div>
							</div>
						}
					/>

					{/* Second Row */}
					<AdContentRowWrapper
						xGap={"gap-x-0"}
						yGap="gap-y-0"
						roundedBorderLeftCard="rounded-tl-2xl rounded-tr-2xl sm:rounded-tr-none rounded-bl-none sm:rounded-bl-2xl"
						roundedBorderRightCard="rounded-tr-none sm:rounded-tr-2xl rounded-br-2xl rounded-bl-2xl sm:rounded-bl-none"
						leftChild={
							<div className=" bg-white p-4 rounded-tl-2xl rounded-tr-2xl sm:rounded-tr-none rounded-bl-none sm:rounded-bl-2xl h-full">
								<AdContentCard
									title={"SPECIAL OFFER"}
									titleColor="!text-gray-400"
									subtitle="New patient discount"
									subtitleColor="!text-green-600"
									contentText="Get 50% off your first consultation and prescription refill. Limited time offer."
									contentTextColor="!text-black"
								/>
							</div>
						}
						rightChild={
							<Image
								src={specialOfferBackground}
								className="rounded-tr-none sm:rounded-tr-2xl rounded-br-2xl rounded-bl-2xl sm:rounded-bl-none w-full h-[14.5rem] sm:h-full object-cover"
								alt="Special Offer Background"
								priority
							/>
						}
					/>
				</section>
			</WrapperMain>
		</>
	);
}

const healthHomePageValues = {
	name: "ToggleHealth",
	industryMessages: "Trusted by over 100,000 patients nationwide",
	healthServicesArr: [
		{ imgSrc: prescriptions, title: "Prescriptions" },
		{ imgSrc: telemedicine, title: "Telemedicine" },
		{ imgSrc: pharmacy, title: "Pharmacy" },
		{ imgSrc: wellness, title: "Wellness" },
		{ imgSrc: insurance, title: "Insurance" },
	],
	healthServicesArrOnHover: [
		{ imgSrc: prescriptionsOnHover, title: "Prescriptions" },
		{ imgSrc: telemedicineOnHover, title: "Telemedicine" },
		{ imgSrc: pharmacyOnHover, title: "Pharmacy" },
		{ imgSrc: wellnessOnHover, title: "Wellness" },
		{ imgSrc: insuranceOnHover, title: "Insurance" },
	],
};

const AdContentRowWrapper = ({
	leftChild,
	rightChild,
	xGap = "gap-x-8",
	yGap = "gap-y-10 sm:gap-y-0 ",
	roundedBorderLeftCard = "rounded-2xl",
	roundedBorderRightCard = "rounded-2xl",
}: {
	leftChild: ReactElement;
	rightChild: ReactElement;
	xGap?: string;
	yGap?: string;
	roundedBorderLeftCard?: string;
	roundedBorderRightCard?: string;
}) => {
	return (
		<section className={`flex flex-col sm:flex-row ${yGap} ${xGap}`}>
			<div className={`w-full sm:w-1/3 ${roundedBorderLeftCard} shadow-2xl`}>
				{leftChild}
			</div>
			<div className={`w-full sm:w-2/3 ${roundedBorderRightCard} shadow-2xl`}>
				{rightChild}
			</div>
		</section>
	);
};

const AdContentCard = ({
	title,
	titleColor,
	subtitle,
	subtitleColor,
	contentText,
	contentTextColor,
}: {
	title: string;
	titleColor?: string;
	subtitle: string;
	subtitleColor?: string;
	contentText: string;
	contentTextColor?: string;
}) => {
	return (
		<div className="flex flex-col gap-y-6 my-auto h-full justify-center ">
			<div
				className={`mx-8 text-sm text-gray-300 tracking-widest font-sohnelight ${titleColor}`}
			>
				{title}
			</div>
			<div
				className={`mx-8 mt-4 text-white font-sohne text-xl ${subtitleColor}`}
			>
				{subtitle}
			</div>
			<div
				className={`text-gray-300 mx-8 mb-4 font-sohne text-md ${contentTextColor}`}
			>
				{contentText}
			</div>
		</div>
	);
}; 