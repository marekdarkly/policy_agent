export const TOGGLEBANK_CHATBOT_AI_EXPERIMENTATION_KEY = "ai-config-experiment"
export const TOGGLEBANK_SIGNUP_FLOW_EXPERIMENTATION_KEY = "togglebank-signup-flow-funnel-experiment"

export const SIGN_UP_STARTED = "sign-up-started";
export const INITIAL_SIGN_UP_COMPLETED = "initial-sign-up-completed";
export const SIGN_UP_PERSONAL_DETAIL_COMPLETED = "sign-up-personal-detail-completed";
export const SIGNUP_COMPLETED = "sign-up-completed";

export const AI_CHATBOT_GOOD_SERVICE = "AI chatbot good service";   
export const AI_CHATBOT_BAD_SERVICE = "AI Chatbot Bad Service";

export const STOCK_API_ERROR_RATES = "stocks-api-error-rates";
export const STOCK_API_LATENCY = "stocks-api-latency";
export const RECENT_TRADES_DB_ERRORS = "recent-trades-db-errors";
export const RECENT_TRADES_DB_LATENCY = "recent-trades-db-latency";

export const BAYESIAN = "bayesian";
export const FREQUENTIST = "frequentist";

export const experimentTypeIterations = {
	[BAYESIAN]: 500,
	[FREQUENTIST]: 10000,
};
