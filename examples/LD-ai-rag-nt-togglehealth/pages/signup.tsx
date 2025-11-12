"use client";

import type React from "react";
import { useFlags, useLDClient } from "@/utils/industryHook";
import { useState, useContext } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSignup } from "@/components/SignUpProvider";
import { COMPANY_LOGOS, HEALTH } from "@/utils/constants";
import Image from "next/image";
import WrapperMain from "@/components/ui/WrapperMain";
import LiveLogsContext from "@/utils/contexts/LiveLogsContext";
import { ThinBanner } from "@/components/ui/thin-banner";
import { INITIAL_SIGN_UP_COMPLETED } from "@/components/generators/experimentation-automation/experimentationConstants";
import { RELEASE_NEW_SIGNUP_PROMO_LDFLAG_KEY } from "@/utils/flagConstants";

export default function SignUpPage() {
	const router = useRouter();
	const ldClient = useLDClient();
	const { userData, updateUserData } = useSignup();
	const [email, setEmail] = useState(userData.email);
	const [password, setPassword] = useState(userData.password);
	const [acceptedTerms, setAcceptedTerms] = useState(true);
	const [error, setError] = useState("");
	const releaseNewSignUpPromoLDFlag = useFlags()[RELEASE_NEW_SIGNUP_PROMO_LDFLAG_KEY];
	const { logLDMetricSent } = useContext(LiveLogsContext);
	const currentDatePlus30 = new Date(
		new Date().setDate(new Date().getDate() + 30)
	).toLocaleDateString();
	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault();

		if (!email || !password) {
			setError("Please fill in all fields");
			return;
		}

		if (!acceptedTerms) {
			setError("Please accept the terms and conditions");
			return;
		}

		updateUserData({ email, password });
		ldClient?.track(INITIAL_SIGN_UP_COMPLETED);
		logLDMetricSent({ metricKey: INITIAL_SIGN_UP_COMPLETED });
		router.push("/personal-details");
	};

	return (
		<WrapperMain className={`flex flex-col px-0`}>
			<ThinBanner
				text={`Sign up today and get your first consultation free! Offer ends on ${currentDatePlus30}`}
				variant="default"
				className="w-full block sm:hidden text-center bg-gradient-to-r from-white via-green-50 to-green-100 text-green-600"
				showCloseButton={false}
				image={{
					src: "/health/icons/prescriptions.svg",
					alt: "Health icon",
				}}
				imageSize={50}
			/>
			<div
				className={`flex px-4 sm:px-0 h-full ${
					releaseNewSignUpPromoLDFlag ? " p-0" : " items-center justify-center"
				}`}
			>
				{/* Left side - Sign up form */}
				<div
					className={`flex items-center justify-center w-full flex-col p-8  ${
						releaseNewSignUpPromoLDFlag && "md:w-7/12 md:p-12"
					}`}
				>
					<Link href="/" title="Go Home">
						<Image
							src={COMPANY_LOGOS[HEALTH].horizontal}
							alt="ToggleHealth Logo"
							className=" mb-10 h-10"
							priority
							style={{
								maxWidth: "100%",
								width: "auto",
							}}
						/>
					</Link>

					{/* Heading */}
					<h1 className="mb-8 text-2xl text-center font-bold text-gray-800 md:text-3xl">
						Start your health journey in less than five minutes
					</h1>

					{/* Form */}
					<form onSubmit={handleSubmit} className="space-y-4">
						{error && (
							<div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
								{error}
							</div>
						)}
						<div>
							<input
								type="email"
								placeholder="Email"
								value={email}
								onChange={(e) => setEmail(e.target.value)}
								className="w-full rounded-md border border-gray-300 p-3 focus:border-blue-500 focus:outline-none"
								readOnly
								onFocus={(e) => {
									(e.target as HTMLInputElement).removeAttribute("readOnly");
								}}
							/>
						</div>
						<div>
							<input
								type="password"
								placeholder="Password"
								value={password}
								onChange={(e) => setPassword(e.target.value)}
								className="w-full rounded-md border border-gray-300 p-3 focus:border-blue-500 focus:outline-none"
								readOnly
								onFocus={(e) => {
									(e.target as HTMLInputElement).removeAttribute("readOnly");
								}}
							/>
						</div>
						<div className="flex items-start">
							<input
								type="checkbox"
								id="terms"
								checked={acceptedTerms}
								onChange={(e) => setAcceptedTerms(e.target.checked)}
								className="mt-1 h-4 w-4 rounded border-gray-300"
							/>
							<label htmlFor="terms" className="ml-2 text-sm text-gray-600">
								I accept the{" "}
								<Link href="#" className="text-green-600 hover:underline">
									Terms of Service
								</Link>{" "}
								and{" "}
								<Link href="#" className="text-green-600 hover:underline">
									Privacy Policy
								</Link>
							</label>
						</div>
						<div className="mt-8 flex flex-col items-center">
							<button
								type="submit"
								className="w-full rounded-full bg-green-600 py-3 text-center font-medium text-white transition-colors hover:bg-green-700"
							>
								Sign Up
							</button>
							<Link
								href="/"
								className="mt-4 text-sm text-gray-500 hover:text-gray-700"
								title="Go Home"
							>
								Back
							</Link>
						</div>
					</form>

					{/* Login link */}
					<div className="mt-6 text-center text-sm">
						Already have an account?{" "}
						<Link href="/" className="text-green-600 hover:underline">
							Log in
						</Link>
					</div>
				</div>

				{/* Right side - Promo */}
				{releaseNewSignUpPromoLDFlag && (
					<div className={`relative  w-5/12 h-[100vh] hidden sm:block `}>
						<div className="w-full aspect-[9/16] bg-gradient-to-br from-white via-green-50 to-green-100 h-full p-4 shadow-lg">
							<div className="flex items-start justify-center h-full">
								<div className="absolute bottom-[50%] left-[3rem]  text-start z-10">
									<h2 className="text-3xl text-green-600">
										Sign up today and get
									</h2>
									<p className="text-3xl font-semibold text-green-700">
										Free Consultation
									</p>
									<p className="mt-6 text-sm text-gray-600">
										Offer ends {currentDatePlus30}
									</p>
								</div>
								<Image
									src={"/health/icons/prescriptions.svg"}
									alt="Health Offer Banner"
									width={100}
									height={100}
									priority
									className={` absolute bottom-[10%] lg:bottom-[5%] left-0 w-[80%]`}
								/>
								<Image
									src={"/health/icons/wellness.svg"}
									alt="Health Offer Banner"
									width={100}
									height={100}
									priority
									className={`absolute bottom-[18%] lg:bottom-[18%] left-[40%] lg:left-[40%] w-[60%]`}
								/>
							</div>
						</div>
					</div>
				)}
			</div>
		</WrapperMain>
	);
}
