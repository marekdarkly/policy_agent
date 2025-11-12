import { Card, CardContent, CardHeader, CardTitle } from "../card";
import { Badge } from "../badge";
import { Button } from "../button";
import { motion } from "framer-motion";

export const FederatedCrisisAccount = () => {
	return (
		<motion.div
			whileHover={{ scale: 1.02 }}
			className="w-full"
		>
			<Card className="border-2 border-purple-300 bg-purple-50">
				<CardHeader className="pb-3">
					<div className="flex items-center justify-between">
						<CardTitle className="text-lg font-semibold text-purple-800">
							Federated Crisis Services
						</CardTitle>
						<Badge className="bg-purple-100 text-purple-800">
							Connected
						</Badge>
					</div>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="grid grid-cols-2 gap-4 text-sm">
						<div>
							<p className="text-gray-600">Crisis Hotlines</p>
							<p className="font-semibold text-purple-700">3 Connected</p>
						</div>
						<div>
							<p className="text-gray-600">Emergency Services</p>
							<p className="font-semibold text-purple-700">2 Connected</p>
						</div>
						<div>
							<p className="text-gray-600">Support Groups</p>
							<p className="font-semibold text-purple-700">5 Connected</p>
						</div>
						<div>
							<p className="text-gray-600">Last Sync</p>
							<p className="font-semibold text-purple-700">2 hours ago</p>
						</div>
					</div>
					
					<div className="text-xs text-gray-500 space-y-1">
						<p>• National Suicide Prevention Lifeline</p>
						<p>• Crisis Text Line</p>
						<p>• Local Emergency Services</p>
						<p>• Community Support Groups</p>
					</div>
					
					<Button
						variant="outline"
						size="sm"
						className="w-full border-purple-400 text-purple-700 hover:bg-purple-100"
					>
						Manage Connections
					</Button>
				</CardContent>
			</Card>
		</motion.div>
	);
};
