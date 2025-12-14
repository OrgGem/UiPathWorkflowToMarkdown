/**
 * Represents a discovered XAML file with metadata
 */
export interface XamlFile {
  path: string;
  size: number;
  checksum: string;
  content: string;
  selected?: boolean;
  llmProcessed?: boolean;
  llmContent?: string;
}

/**
 * Configuration for LLM processing
 */
export interface LLMConfig {
  enabled: boolean;
  apiKey: string;
  baseUrl: string;
  prompt: string;
}

/**
 * Backend API configuration
 */
export interface BackendConfig {
  use_llm: boolean;
  llm_provider?: string;
  api_key?: string;
  base_url?: string;
}

/**
 * OpenAI-compatible chat completion request
 */
export interface ChatCompletionRequest {
  model: string;
  messages: Array<{
    role: 'system' | 'user' | 'assistant';
    content: string;
  }>;
  temperature?: number;
}

/**
 * OpenAI-compatible chat completion response
 */
export interface ChatCompletionResponse {
  choices: Array<{
    message: {
      role: string;
      content: string;
    };
  }>;
}
