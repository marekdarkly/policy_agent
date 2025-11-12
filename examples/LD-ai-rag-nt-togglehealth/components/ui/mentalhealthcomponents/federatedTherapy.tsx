import { Card, CardContent, CardHeader, CardTitle } from "../card";
import { Badge } from "../badge";
import { Button } from "../button";
import { motion } from "framer-motion";

export const FederatedTherapyAccount = () => {
	return (
		<motion.div
			whileHover={{ scale: 1.02 }}
			className="w-full"
		>
			<Card className="border-2 border-blue-300 bg-blue-50">
				<CardHeader className="pb-3">
					<div className="flex items-center justify-between">
						<CardTitle className="text-lg font-semibold text-blue-800">
							Federated Therapy Services
						</CardTitle>
						<Badge className="bg-blue-100 text-blue-800">
							Connected
						</Badge>
					</div>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="grid grid-cols-2 gap-4 text-sm">
						<div>
							<p className="text-gray-600">Therapists</p>
							<p className="font-semibold text-blue-700">2 Connected</p>
						</div>
						<div>
							<p className="text-gray-600">Clinics</p>
							<p className="font-semibold text-blue-700">1 Connected</p>
						</div>
						<div>
							<p className="text-gray-600">Online Platforms</p>
							<p className="font-semibold text-blue-700">3 Connected</p>
						</div>
						<div>
							<p className="text-gray-600">Last Sync</p>
							<p className="font-semibold text-blue-700">1 day ago</p>
						</div>
					</div>
					
					<div className="text-xs text-gray-500 space-y-1">
						<p>• Dr. Sarah Johnson - CBT Specialist</p>
						<p>• Dr. Michael Chen - Psychiatrist</p>
						<p>• BetterHelp Online Therapy</p>
						<p>• Talkspace Platform</p>
					</div>
					
					<Button
						variant="outline"
						size="sm"
						className="w-full border-blue-400 text-blue-700 hover:bg-blue-100"
					>
						Manage Connections
					</Button>
				</CardContent>
			</Card>
		</motion.div>
	);
};
