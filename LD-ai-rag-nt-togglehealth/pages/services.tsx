"use client";

import React, { useContext } from "react";
import { useLDClient } from "@/utils/industryHook";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSignup } from "@/components/SignUpProvider";
import WrapperMain from "@/components/ui/WrapperMain";
import SignUpProgressIndicator from "@/components/ui/bankcomponents/SignUpProgressIndicator";
import { COMPANY_LOGOS, HEALTH } from "@/utils/constants";
import Image from "next/image";
import LiveLogsContext from "@/utils/contexts/LiveLogsContext";
import { SIGNUP_COMPLETED } from "@/components/generators/experimentation-automation/experimentationConstants";

const services = [
	"Telemedicine",
	"Prescription Management",
	"Pharmacy Services",
	"Mental Health",
	"Preventive Care",
	"Specialist Referrals",
	"Lab Services",
	"Insurance Coordination",
];

export default function ServicesPage() {
	const router = useRouter();
	const { userData, toggleService } = useSignup();
	const [error, setError] = useState("");
	const ldClient = useLDClient();
	const { logLDMetricSent } = useContext(LiveLogsContext);

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault();

		if (userData.selectedServices.length === 0) {
			setError("Please select at least one service");
			return;
		}
		ldClient?.track(SIGNUP_COMPLETED);
		logLDMetricSent({ metricKey: SIGNUP_COMPLETED });

		// Navigate to a success page or dashboard
		router.push("/success");
	};

	const isSelected = (service: string) => {
		return userData.selectedServices.includes(service);
	};

	return (
		<WrapperMain className="flex flex-col items-center justify-center py-4">
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
			{/* Progress indicator */}
			<SignUpProgressIndicator pageNumber={3} />

			{/* Heading */}
			<div className="mb-8 text-center">
				<h1 className="mb-2 text-2xl font-bold text-gray-800">
					What health services do you need?
				</h1>
				<p className="text-sm text-gray-600">Select all that apply</p>
			</div>

			{/* Form */}
			<form onSubmit={handleSubmit} className="w-full ">
				{error && (
					<div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-600">
						{error}
					</div>
				)}

				<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
					{services.map((service) => (
						<button
							key={service}
							type="button"
							onClick={() => toggleService(service)}
							className={`flex h-20 items-center justify-center rounded-lg border p-4 text-center transition-colors ${
								isSelected(service)
									? "border-green-600 bg-green-50 text-green-700"
									: "border-gray-200 bg-white text-gray-800 hover:bg-gray-50"
							}`}
						>
							{service}
						</button>
					))}
				</div>

				{/* Buttons */}
				<div className="mt-8 flex flex-col items-center">
					<button
						type="submit"
						className="w-full max-w-xs rounded-full bg-green-600 py-3 text-center font-medium text-white transition-colors hover:bg-green-700"
					>
						Complete Setup
					</button>
					<Link
						href="/personal-details"
						className="mt-4 text-sm text-gray-500 hover:text-gray-700"
					>
						Back
					</Link>
				</div>
			</form>
		</WrapperMain>
	);
}
