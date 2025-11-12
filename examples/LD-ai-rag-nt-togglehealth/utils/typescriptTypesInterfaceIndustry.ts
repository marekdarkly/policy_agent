export type WealthManagementGraphDataType = {
	month: string;
	balance: number;
};

export type WellnessManagementGraphDataType = {
	month: string;
	wellnessScore: number;
};

export interface TransactionInterface {
	id: number;
	date: string;
	merchant: string;
	status: string;
	amount: number;
	accounttype: string;
	user: string;
}

export interface AIModelInterface {
	messages: [
		{
			content: string;
			role: "system" | "user";
		}
	];
	model: {
		parameters: { temperature: number; maxTokens: number };
		name: string;
	};
	_ldMeta: {
		enabled: boolean;
		variationKey?: string;
		version?: number;
		versionKey?: string;
	};
}

type AIChatBotConversationRole = "assistant" | "user" | "system";
export interface ChatBotMessageInterface {
	id?: string;
	role: AIChatBotConversationRole;
	content: string;
	customStyle?: string;
}
export interface ChatBotAIApiResponseInterface {
	error?: string;
	response: string;
	enabled: boolean;
	modelName: string;
	requestId?: string;
	pendingMetrics?: boolean;
	metrics?: {
		grounding_score?: number;
		grounding_threshold?: number;
		relevance_score?: number;
		relevance_threshold?: number;
		processing_latency_ms?: number;
		contextual_grounding_units?: number;
		characters_guarded?: number;
		total_characters?: number;
		model_used?: string;
		knowledge_base_id?: string;
		guardrail_id?: string;
		factual_accuracy_score?: any;
		input_tokens?: number;
		output_tokens?: number;
		judge_model_name?: string;
		judge_input_tokens?: number;
		judge_output_tokens?: number;
		// Detailed judge breakdown components
		judge_reasoning?: string;
		factual_claims?: string[];
		accurate_claims?: string[];
		inaccurate_claims?: string[];
	};
}

export interface UserChatInputResponseInterface {
	aiConfigKey: string;
	userInput: string;
}

export interface UserAIChatBotFeedbackResponseInterface {
	aiConfigKey: string;
	feedback: string;
}

export interface StockDataInterface {
	time: string;
	value: number;
	direction: "up" | "down" | null;
}

export interface StockInterface {
	ticker: string;
	name: string;
	data: StockDataInterface[];
	image: string;
}

export interface WealthManagementSheetInterface {
	data: any;
	aiPrompt: string;
	submitQuery: (prompt: string) => void;
	prompt: string;
	loading: boolean;
	aiResponse: string;
}

export type UserDataType = {
	email: string;
	password: string;
	firstName: string;
	lastName: string;
	dob: string;
	ssn: string;
	phone: string;
	address: string;
	apt: string;
	zip: string;
	selectedServices: string[];
};
