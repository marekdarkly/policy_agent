import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

export const PharmacyAccount = () => {
	const [pharmacyBalance, setPharmacyBalance] = useState(125.50);
	const [monthlySpending, setMonthlySpending] = useState(85.00);

	return (
		<div className="h-full flex flex-col">
			<CardHeader className="pb-3">
				<div className="flex items-center justify-between">
					<CardTitle className="text-lg font-semibold text-purple-600">
						Pharmacy Services
					</CardTitle>
					<Badge variant="secondary" className="bg-purple-100 text-purple-800">
						Active
					</Badge>
				</div>
			</CardHeader>
			<CardContent className="flex-1 flex flex-col">
				<div className="space-y-4">
					<div className="text-center">
						<p className="text-2xl font-bold text-purple-600">
							${pharmacyBalance.toFixed(2)}
						</p>
						<p className="text-sm text-gray-500">Available Balance</p>
					</div>
					
					<div className="space-y-2">
						<div className="flex items-center justify-between">
							<span className="text-sm text-gray-600">Monthly Spending</span>
							<span className="text-sm font-medium">${monthlySpending.toFixed(2)}</span>
						</div>
						<Progress value={70} className="h-2" />
					</div>
					
					<div className="space-y-3">
						<div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">CVS Pharmacy</p>
								<p className="text-xs text-gray-500">Last visit: 2 days ago</p>
							</div>
							<Badge variant="outline" className="text-purple-600 border-purple-600">
								Preferred
							</Badge>
						</div>
						
						<div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">Walgreens</p>
								<p className="text-xs text-gray-500">Last visit: 1 week ago</p>
							</div>
							<Badge variant="outline" className="text-purple-600 border-purple-600">
								Active
							</Badge>
						</div>
						
						<div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
							<div>
								<p className="font-medium text-sm">Rite Aid</p>
								<p className="text-xs text-gray-500">Last visit: 3 weeks ago</p>
							</div>
							<Badge variant="outline" className="text-gray-600 border-gray-600">
								Inactive
							</Badge>
						</div>
					</div>
					
					<div className="mt-auto pt-4 space-y-2">
						<Button className="w-full bg-purple-600 hover:bg-purple-700">
							Find Pharmacy
						</Button>
						<Button variant="outline" className="w-full">
							Transfer Prescriptions
						</Button>
					</div>
				</div>
			</CardContent>
		</div>
	);
}; 