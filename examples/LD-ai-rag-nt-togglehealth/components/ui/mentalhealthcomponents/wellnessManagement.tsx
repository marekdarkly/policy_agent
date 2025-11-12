import { useState } from "react";
import { Button } from "../button";
import { Card, CardContent, CardHeader, CardTitle } from "../card";
import { Textarea } from "../input";
import { Label } from "../label";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "../sheet";
import { Badge } from "../badge";

interface WellnessManagementSheetProps {
	onSubmit: (query: any) => Promise<string | undefined>;
	loading: boolean;
	aiResponse: string;
	viewPrompt: string;
}

export default function WellnessManagementSheet({
	onSubmit,
	loading,
	aiResponse,
	viewPrompt,
}: WellnessManagementSheetProps) {
	const [open, setOpen] = useState(false);
	const [query, setQuery] = useState("");

	const handleSubmit = async () => {
		if (query.trim()) {
			await onSubmit(query);
			setQuery("");
		}
	};

	return (
		<Sheet open={open} onOpenChange={setOpen}>
			<SheetTrigger asChild>
				<Button variant="outline" className="border-purple-300 text-purple-700 hover:bg-purple-50">
					Mental Wellness AI
				</Button>
			</SheetTrigger>
			<SheetContent className="w-[400px] sm:w-[540px]">
				<SheetHeader>
					<SheetTitle className="text-purple-800">Mental Wellness AI Assistant</SheetTitle>
					<SheetDescription>
						Get personalized insights about your mental health data and wellness journey.
					</SheetDescription>
				</SheetHeader>
				<div className="grid gap-4 py-4">
					<div className="grid gap-2">
						<Label htmlFor="query" className="text-purple-700 font-semibold">
							Ask about your mental wellness:
						</Label>
						<Textarea
							id="query"
							placeholder="e.g., How is my crisis monitoring performing? What patterns do you see in my therapy sessions?"
							value={query}
							onChange={(e) => setQuery(e.target.value)}
							className="min-h-[100px] border-purple-200 focus:border-purple-400"
						/>
					</div>
					<Button
						onClick={handleSubmit}
						disabled={loading || !query.trim()}
						className="bg-purple-600 hover:bg-purple-700 text-white"
					>
						{loading ? "Analyzing..." : "Get Analysis"}
					</Button>
					{aiResponse && (
						<Card className="border-purple-200">
							<CardHeader>
								<CardTitle className="text-purple-800 text-lg">AI Analysis</CardTitle>
							</CardHeader>
							<CardContent>
								<p className="text-gray-700 leading-relaxed">{aiResponse}</p>
								<div className="mt-3">
									<Badge variant="outline" className="text-purple-600 border-purple-300">
										Mental Health AI
									</Badge>
								</div>
							</CardContent>
						</Card>
					)}
					<div className="text-xs text-gray-500 mt-4 p-3 bg-purple-50 rounded-lg">
						<p className="font-semibold text-purple-700 mb-2">Suggested Questions:</p>
						<ul className="space-y-1 text-gray-600">
							<li>• How is my crisis monitoring performing?</li>
							<li>• What patterns do you see in my therapy sessions?</li>
							<li>• How can I improve my medication adherence?</li>
							<li>• What wellness trends should I be aware of?</li>
						</ul>
					</div>
				</div>
			</SheetContent>
		</Sheet>
	);
}
