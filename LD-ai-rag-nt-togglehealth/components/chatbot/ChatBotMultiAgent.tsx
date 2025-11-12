import { useEffect, useState, useRef, useContext, useCallback } from "react";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardHeader,
	CardContent,
	CardFooter,
} from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import LoginContext from "@/utils/contexts/login";
import { v4 as uuidv4 } from "uuid";
import { PulseLoader } from "react-spinners";
import { useToast } from "@/components/ui/use-toast";
import { useIsMobile } from "../hooks/use-mobile";
import { Sheet, SheetContent, SheetClose, SheetTitle } from "@/components/ui/sheet";
import { useSidebar } from "../ui/sidebar";
import { cn } from "@/utils/utils";
import { motion, AnimatePresence } from "framer-motion";

interface ChatMessage {
	role: "user" | "assistant" | "system" | "status";
	content: string;
	id: string;
	customStyle?: string;
}

interface AgentStatusInfo {
	status: string;  // "routing", "specialist", "brand_voice", "complete"
	agent?: string;
	message: string;
}

interface ChatResponse {
	response: string;
	modelName: string;
	enabled: boolean;
	requestId: string;
	agentFlow?: Array<{agent: string; status: string; [key: string]: any}>;
	metrics?: any;
	pendingMetrics?: boolean;
	error?: string;
}

function ChatBotMultiAgentInterface({
	cardRef,
	isOpen,
	toggleSidebar,
}: {
	cardRef: React.RefObject<HTMLDivElement>;
	isOpen: boolean;
	toggleSidebar: (boolean?: boolean) => void;
}) {
	const [messages, setMessages] = useState<ChatMessage[]>([]);
	const [userInput, setUserInput] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const [agentStatus, setAgentStatus] = useState<AgentStatusInfo | null>(null);
	const [lastMetrics, setLastMetrics] = useState<any>(null);
	const [showMetrics, setShowMetrics] = useState(false);
	const [chatHeaderHeight, setChatHeaderHeight] = useState(0);
	const [chatFooterHeight, setChatFooterHeight] = useState(0);
	
	const isMobile = useIsMobile();
	const { toast } = useToast();
	const { userObject } = useContext(LoginContext);
	const chatContentRef = useRef<HTMLDivElement>(null);
	const chatHeaderRef = useRef<HTMLDivElement>(null);
	const chatFooterRef = useRef<HTMLDivElement>(null);
	const { open } = useSidebar();

	useEffect(() => {
		if (chatContentRef.current) {
			chatContentRef.current.scrollTop = chatContentRef.current.scrollHeight;
		}
	}, [messages, agentStatus]);

	useEffect(() => {
		if (chatHeaderRef.current?.offsetHeight) {
			setChatHeaderHeight(chatHeaderRef?.current?.offsetHeight);
		}
	}, [chatHeaderHeight]);

	useEffect(() => {
		if (chatFooterRef.current?.offsetHeight) {
			setChatFooterHeight(chatFooterRef?.current?.offsetHeight);
		}
	}, [chatFooterHeight]);

	const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		setUserInput(e.target.value);
	};

	const getAgentStatusMessage = (status: AgentStatusInfo | null): string => {
		if (!status) return "";
		
		switch (status.status) {
			case "routing":
				return "🔍 Analyzing your question...";
			case "specialist":
				if (status.agent?.includes("policy")) {
					return "📋 Reaching out to Policy Specialist...";
				} else if (status.agent?.includes("provider")) {
					return "🏥 Reaching out to Provider Specialist...";
				} else if (status.agent?.includes("scheduler")) {
					return "📅 Reaching out to Scheduler Specialist...";
				}
				return "👔 Reaching out to specialist...";
			case "brand_voice":
				return "✨ Putting an answer together...";
			default:
				return status.message || "Processing...";
		}
	};

	const submitChatBotQuery = async () => {
		if (!userInput.trim()) return;

		const currentInput = userInput;
		setIsLoading(true);
		setUserInput("");
		setShowMetrics(false);

		// Display the user's message
		const userMessage: ChatMessage = {
			role: "user",
			content: currentInput,
			id: uuidv4().slice(0, 4),
		};

		setMessages(prevMessages => [...prevMessages, userMessage]);

		// Show initial status
		setAgentStatus({
			status: "routing",
			message: "Analyzing your question..."
		});

		try {
			const response = await fetch("/api/chat-multiagent", {
				method: "POST",
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					aiConfigKey: "policy_multiagent",
					userInput: currentInput,
				}),
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({ error: 'Failed to parse error response' }));
				throw new Error(errorData.error || `Request failed with status ${response.status}`);
			}

			const data: ChatResponse = await response.json();

			// Simulate agent progression through the flow
			if (data.agentFlow && data.agentFlow.length > 0) {
				for (let i = 0; i < data.agentFlow.length; i++) {
					const agent = data.agentFlow[i];
					
					if (agent.agent === "triage_router") {
						setAgentStatus({
							status: "routing",
							agent: agent.agent,
							message: "Analyzing your question..."
						});
						await new Promise(resolve => setTimeout(resolve, 300));
					} else if (agent.agent.includes("specialist")) {
						setAgentStatus({
							status: "specialist",
							agent: agent.agent,
							message: `Reaching out to ${agent.agent.replace("_", " ")}...`
						});
						await new Promise(resolve => setTimeout(resolve, 500));
					} else if (agent.agent === "brand_voice") {
						setAgentStatus({
							status: "brand_voice",
							agent: agent.agent,
							message: "Putting an answer together..."
						});
						await new Promise(resolve => setTimeout(resolve, 300));
					}
				}
			}

			// Clear status and show response
			setAgentStatus(null);

			const assistantMessage: ChatMessage = {
				role: "assistant",
				content: data.response || "I'm sorry. Please try again.",
				id: uuidv4().slice(0, 4),
			};

			setMessages(prevMessages => [...prevMessages, assistantMessage]);

			// Store metrics
			if (data.metrics) {
				setLastMetrics(data.metrics);
			}

		} catch (error) {
			console.error("Chat query failed:", error);
			setAgentStatus(null);
			
			const errorMessage: ChatMessage = {
				role: "assistant",
				content: error instanceof Error ? error.message : "An unexpected error occurred.",
				id: uuidv4().slice(0, 4),
			};
			setMessages(prevMessages => [...prevMessages, errorMessage]);
		} finally {
			setIsLoading(false);
		}
	};

	return (
		<>
			{isOpen && (
				<div
					ref={cardRef}
					className={cn(
						"relative lg:fixed lg:inset-4 lg:z-50 flex items-center justify-center p-0 max-w-full",
						open && "right-0 lg:right-[30vw]"
					)}
				>
					<Card className="w-full lg:w-[80vw] lg:h-[80vh] lg:mx-auto">
						<CardHeader
							className="flex flex-row items-center"
							ref={chatHeaderRef}
						>
							<div className="flex items-center space-x-4">
								<Avatar>
									<img
										src={"/personas/ToggleAvatar.png"}
										alt="Chatbot Avatar"
									/>
									<AvatarFallback>AI</AvatarFallback>
								</Avatar>
								<div>
									<p className="text-xl font-medium leading-none">
										ToggleHealth Assistant
									</p>
									<p className="text-base text-gray-500 dark:text-gray-400">
										Powered by <span className="font-bold">Multi-Agent AI</span> with <span className="text-amazonColor font-bold">Amazon Bedrock</span>
									</p>
								</div>
							</div>
							<div className="ml-auto flex items-center space-x-2">
								<Button
									variant="ghost"
									size="icon"
									className="ml-auto rounded-full hidden lg:block"
									onClick={() => toggleSidebar(false)}
								>
									<XIcon className="h-6 w-6" />
									<span className="sr-only">Close Chatbot</span>
								</Button>
							</div>
						</CardHeader>
						<CardContent
							className={`lg:h-[calc(80vh-200px)] overflow-y-auto text-lg`}
							ref={chatContentRef}
							style={
								isMobile
									? {
											height: `calc(100vh - ${
												chatHeaderHeight + chatFooterHeight + 40
											}px)`,
									  }
									: {}
							}
						>
							<div className="space-y-6">
								<div className="flex w-max max-w-[75%] flex-col gap-2 rounded-lg px-4 py-3 text-lg bg-gray-100 dark:bg-gray-800">
									{userObject && userObject.personaname
										? `Hello ${userObject.personaname}! How can I assist you with your health insurance today?`
										: "Hello! How can I assist you with your health insurance today?"}
								</div>
								
								{messages.map((m) => {
									if (m.role === "assistant") {
										return (
											<div
												key={m.id}
												className="flex w-max max-w-[75%] flex-col gap-2 rounded-lg px-4 py-3 text-lg bg-gray-100 dark:bg-gray-800"
											>
												{m.content}
											</div>
										);
									}

									return (
										<div
											key={m.id}
											className="flex w-max max-w-[75%] flex-col gap-2 rounded-lg px-4 py-3 text-lg ml-auto bg-gradient-airways text-white dark:bg-gray-50 dark:text-gray-900"
										>
											{m.content}
										</div>
									);
								})}

								{/* Agent Status Box */}
								<AnimatePresence>
									{agentStatus && (
										<motion.div
											initial={{ opacity: 0, y: 10 }}
											animate={{ opacity: 1, y: 0 }}
											exit={{ opacity: 0, y: -10 }}
											className="flex w-max max-w-[75%] flex-col gap-2 rounded-lg px-4 py-3 text-sm bg-blue-50 dark:bg-blue-900 border-2 border-blue-200 dark:border-blue-700"
										>
											<div className="flex items-center gap-2">
												<PulseLoader size={6} color="#3B82F6" />
												<span className="text-blue-700 dark:text-blue-200 font-medium">
													{getAgentStatusMessage(agentStatus)}
												</span>
											</div>
										</motion.div>
									)}
								</AnimatePresence>

								{/* Metrics Display */}
								{lastMetrics && (
									<div className="mt-4 border-t pt-2">
										<Button
											variant="ghost"
											size="sm"
											onClick={() => setShowMetrics(!showMetrics)}
											className="text-base text-gray-500 hover:text-gray-700 p-2 h-auto"
										>
											{showMetrics ? '▼' : '▶'} Agent Flow & Metrics
										</Button>
										{showMetrics && (
											<div className="mt-2 text-base text-gray-600 bg-gray-50 dark:bg-gray-800 rounded p-4 space-y-3">
												{/* Agent Flow */}
												{lastMetrics.agent_flow && (
													<div className="border-b pb-2">
														<div className="font-semibold text-gray-700 mb-2">🔄 Agent Flow:</div>
														<div className="flex flex-wrap gap-2">
															{lastMetrics.agent_flow.map((agent: any, idx: number) => (
																<div key={idx} className="bg-blue-100 dark:bg-blue-900 px-3 py-1 rounded-full text-sm">
																	{agent.agent.replace(/_/g, " ")}
																	{agent.rag_docs && ` (${agent.rag_docs} docs)`}
																</div>
															))}
														</div>
													</div>
												)}
												
												{/* Query Type */}
												{lastMetrics.query_type && (
													<div className="flex justify-between">
														<span>Query Type:</span>
														<span className="font-mono text-sm">{lastMetrics.query_type}</span>
													</div>
												)}
											</div>
										)}
									</div>
								)}
							</div>
						</CardContent>
						<CardFooter className="p-4 lg:p-6" ref={chatFooterRef}>
							<form
								onSubmit={(e) => {
									e.preventDefault();
									submitChatBotQuery();
								}}
								className="flex w-full items-center space-x-2"
							>
								<Input
									id="message"
									placeholder="Ask about your health insurance..."
									className="flex-1 text-lg h-12"
									autoComplete="off"
									value={userInput}
									onChange={handleInputChange}
									disabled={isLoading}
								/>
								<Button
									type="submit"
									size="icon"
									className="h-12 w-12"
									disabled={isLoading || !userInput.trim()}
									onClick={submitChatBotQuery}
								>
									<SendIcon className="h-6 w-6" />
									<span className="sr-only">Send</span>
								</Button>
							</form>
						</CardFooter>
					</Card>
				</div>
			)}
		</>
	);
}

export default function ChatBotMultiAgent() {
	const isMobile = useIsMobile();
	const [isOpen, setIsOpen] = useState(false);
	const [openMobile, setOpenMobile] = useState(false);
	const cardRef = useRef<HTMLDivElement>(null);
	const { open } = useSidebar();

	useEffect(() => {
		const handleClickOutside = (event: MouseEvent) => {
			if (cardRef.current && !cardRef.current.contains(event.target as Node)) {
				toggleSidebar(false);
			}
		};

		if (isOpen) {
			document.addEventListener("mousedown", handleClickOutside);
		} else {
			document.removeEventListener("mousedown", handleClickOutside);
		}

		return () => {
			document.removeEventListener("mousedown", handleClickOutside);
		};
	}, [isOpen]);

	const toggleSidebar = useCallback(
		(boolean?: boolean) => {
			if (boolean === false) {
				return isMobile ? setOpenMobile(false) : setIsOpen(false);
			}
			return isMobile
				? setOpenMobile((open) => !open)
				: setIsOpen((open) => !open);
		},
		[isMobile, setIsOpen, setOpenMobile]
	);

	return (
		<>
			<motion.div
				initial={{ opacity: 0 }}
				animate={{ opacity: 1 }}
				transition={{ duration: 1.5 }}
				className={cn(
					"fixed bottom-4 right-4 z-10",
					open && "lg:right-[calc(30vw+1rem)]"
				)}
			>
				<Button
					variant="ghost"
					size="icon"
					className="bg-airlinedarkblue text-gray-50 hover:bg-airlinedarkblue/90 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-50/90 shadow-lg !h-12 !w-12 animate-pulse hover:animate-none"
					onClick={() => toggleSidebar()}
				>
					{isOpen && <XIcon className="h-8 w-8" />}
					{!isOpen && <MessageCircleIcon className="h-8 w-8" />}
					<span className="sr-only">Open Assistant</span>
				</Button>
			</motion.div>
			{isMobile ? (
				<Sheet open={openMobile} onOpenChange={setOpenMobile}>
					<SheetContent
						data-sidebar="sidebar"
						data-mobile="true"
						className="w-full h-full bg-sidebar p-0 text-sidebar-foreground !border-0 [&>button]:hidden"
						side={"right"}
						id="sidebar-mobile"
					>
						<SheetTitle className="sr-only">Health Insurance Assistant</SheetTitle>
						<div className="flex h-full w-full flex-col ">
							<ChatBotMultiAgentInterface
								cardRef={cardRef}
								isOpen={openMobile}
								toggleSidebar={toggleSidebar}
							/>
							<SheetClose className="h-10 w-full bg-airlinedarkblue text-white">
								Close
							</SheetClose>
						</div>
					</SheetContent>
				</Sheet>
			) : (
				<ChatBotMultiAgentInterface
					cardRef={cardRef}
					isOpen={isOpen}
					toggleSidebar={toggleSidebar}
				/>
			)}
		</>
	);
}

function MessageCircleIcon(props: any) {
	return (
		<svg
			{...props}
			xmlns="http://www.w3.org/2000/svg"
			width="24"
			height="24"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="2"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
		</svg>
	);
}

function SendIcon(props: any) {
	return (
		<svg
			{...props}
			xmlns="http://www.w3.org/2000/svg"
			width="24"
			height="24"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="2"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path d="m22 2-7 20-4-9-9-4Z" />
			<path d="M22 2 11 13" />
		</svg>
	);
}

function XIcon(props: any) {
	return (
		<svg
			{...props}
			xmlns="http://www.w3.org/2000/svg"
			width="24"
			height="24"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="2"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path d="M18 6 6 18" />
			<path d="m6 6 12 12" />
		</svg>
	);
}

