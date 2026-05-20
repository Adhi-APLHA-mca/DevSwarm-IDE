/**
 * API Client for DevSwarm Multi-Agent System
 * Handles communication with Backend Agents (CEO, Business Analyst, Code Writer, etc.)
 * Uses Groq API (Llama models) for intelligent LLM-powered question generation
 */

const API_BASE_URL = "http://localhost:8000";

// Add timeout for requests
const FETCH_TIMEOUT = 5000;

export interface Question {
  index: number;
  text: string;
}

export interface InitiateBAResponse {
  status: string;
  client_goal: string;
  questions: string[];
  total_questions: number;
}

export interface AnswerResponse {
  status: string;
  question_index: number;
  answered: number;
  total: number;
  is_complete: boolean;
  message?: string;
  next_question_index?: number;
}

export interface RequirementsResponse {
  status: string;
  message: string;
  requirements: any;
}

export interface StatusResponse {
  has_active_session: boolean;
  client_goal: string;
  questions_count: number;
  answers_count: number;
  is_complete: boolean;
}

class BAAPIClient {
  private baseURL: string = API_BASE_URL;
  private isBackendOnline: boolean = false;

  /**
   * Check if backend is online
   */
  async checkBackendStatus(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT);
      
      const response = await fetch(`${this.baseURL}/health`, { 
        signal: controller.signal 
      });
      clearTimeout(timeoutId);
      
      this.isBackendOnline = response.ok;
      return response.ok;
    } catch (error) {
      console.warn("Backend not reachable:", error);
      this.isBackendOnline = false;
      return false;
    }
  }

  /**
   * Generate dynamic questions using Groq API (Llama model) based on client goal
   * Uses LLM as a Business Analyst to ask intelligent clarifying questions
   */
  private async generateDynamicQuestions(clientGoal: string): Promise<string[]> {
    try {
      // Use Groq API with Llama model - Business Analyst asking clarifying questions
      const apiKey = import.meta.env.REACT_APP_GROQ_API_KEY;
      
      if (apiKey) {
        const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${apiKey}`,
          },
          body: JSON.stringify({
            model: "openai/gpt-oss-120b",
            messages: [
              {
                role: "system",
                content: `You are an expert Business Analyst. Your job is to understand what the customer wants to build and ask intelligent clarifying questions to understand their exact needs. Ask specific, actionable questions that will help you gather comprehensive requirements. Generate 7-9 questions.`,
              },
              {
                role: "user",
                content: `Customer wants to build: "${clientGoal}"\n\nGenerate clarifying questions to understand their requirements better. Respond ONLY with a JSON array: ["Question 1?", "Question 2?", ...]`,
              },
            ],
            temperature: 0.7,
            max_tokens: 1024,
          }),
        });

        if (response.ok) {
          const data = await response.json();
          const content = data.choices[0].message.content;
          const jsonMatch = content.match(/\[[\s\S]*\]/);
          if (jsonMatch) {
            return JSON.parse(jsonMatch[0]);
          }
        }
      }
    } catch (error) {
      console.warn("Groq LLM question generation failed:", error);
    }

    // Fallback: If LLM fails, return empty - force user to have backend
    return [];
  }

  /**
   * Demo questions for offline mode - uses LLM when backend is down
   */
  private async getDemoQuestions(clientGoal: string): Promise<InitiateBAResponse> {
    const questions = await this.generateDynamicQuestions(clientGoal);
    
    // If LLM also fails, show error
    if (questions.length === 0) {
      return {
        status: "error",
        client_goal: clientGoal,
        questions: ["Backend is offline and LLM service unavailable. Please check your Groq API key and internet connection."],
        total_questions: 1,
      };
    }
    
    return {
      status: "success",
      client_goal: clientGoal,
      questions,
      total_questions: questions.length,
    };
  }

  /**
   * Initiate BA conversation with client goal
   */
  async initiate(clientGoal: string, context?: string): Promise<InitiateBAResponse> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT);
      
      const response = await fetch(`${this.baseURL}/ba/initiate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_goal: clientGoal,
          context: context || null,
        }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to initiate: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.warn("Backend offline, using LLM-powered (Groq/Llama) demo mode:", error);
      return this.getDemoQuestions(clientGoal);
    }
  }

  /**
   * Submit answer to a question
   */
  async submitAnswer(questionIndex: number, answer: string): Promise<AnswerResponse> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT);
      
      const response = await fetch(
        `${this.baseURL}/ba/answer`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question_index: questionIndex,
            answer: answer
          }),
          signal: controller.signal
        }
      );
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to submit: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.warn("Backend offline, using demo mode:", error);
      // Return demo response
      return {
        status: "success",
        question_index: questionIndex,
        answered: questionIndex + 1,
        total: 10,
        is_complete: questionIndex + 1 >= 10,
        next_question_index: questionIndex + 1 < 10 ? questionIndex + 1 : undefined
      };
    }
  }

  /**
   * Process all answers and generate requirements
   */
  async processRequirements(): Promise<RequirementsResponse> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT);
      
      const response = await fetch(`${this.baseURL}/ba/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to process: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.warn("Backend offline, using demo mode:", error);
      // Return demo requirements
      return {
        status: "success",
        message: "Requirements processed (Demo Mode - Backend Offline)",
        requirements: {
          summary: {
            project_name: "Sample Project",
            features: ["User Management", "Dashboard", "Analytics", "Reporting"],
            tech_stack: ["React", "Node.js", "PostgreSQL"],
            timeline: "3 months",
            team_size: "5-7 developers"
          }
        }
      };
    }
  }

  /**
   * Get current session status
   */
  async getStatus(): Promise<StatusResponse> {
    const response = await fetch(`${this.baseURL}/ba/status`);

    if (!response.ok) {
      throw new Error(`Failed to get status: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get all questions for current session
   */
  async getQuestions(): Promise<{ questions: string[]; total: number }> {
    const response = await fetch(`${this.baseURL}/ba/questions`);

    if (!response.ok) {
      throw new Error(`Failed to get questions: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get processed requirements
   */
  async getRequirements(): Promise<RequirementsResponse> {
    const response = await fetch(`${this.baseURL}/ba/requirements`);

    if (!response.ok) {
      throw new Error(`Failed to get requirements: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Reset session
   */
  async resetSession(): Promise<{ status: string; message: string }> {
    const response = await fetch(`${this.baseURL}/ba/reset`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error(`Failed to reset session: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Generate professional development plan using CEO Agent
   * Creates a strategic plan from gathered requirements
   */
  async generateDevelopmentPlan(requirements: any, projectGoal: string): Promise<string> {
    try {
      const apiKey = import.meta.env.REACT_APP_GROQ_API_KEY;

      if (apiKey) {
        const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${apiKey}`,
          },
          body: JSON.stringify({
            model: "openai/gpt-oss-120b",
            messages: [
              {
                role: "system",
                content: `You are a strategic CEO and Project Manager. Your role is to create a comprehensive, professional development plan from requirements gathered by the Business Analyst. Format the plan with clear sections: Executive Summary, Project Scope, Development Phases, Resource Requirements, Risk Assessment, and Success Metrics. Be professional, strategic, and provide a clear roadmap.`,
              },
              {
                role: "user",
                content: `Project Goal: "${projectGoal}"\n\nGathered Requirements:\n${JSON.stringify(requirements, null, 2)}\n\nCreate a comprehensive development plan that is professional and actionable.`,
              },
            ],
            temperature: 0.7,
            max_tokens: 2048,
          }),
        });

        if (response.ok) {
          const data = await response.json();
          return data.choices[0].message.content;
        }
      }
    } catch (error) {
      console.warn("CEO plan generation failed:", error);
    }

    // Fallback professional plan
    return `## Development Plan - ${projectGoal}\n\n### Executive Summary\nThe project will be delivered in phases with clear milestones and deliverables.\n\n### Phases\n1. **Planning & Design** - Requirements finalization and architecture design\n2. **Development** - Core feature implementation\n3. **Testing & QA** - Comprehensive testing and bug fixes\n4. **Deployment** - Production release and monitoring`;
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const baApiClient = new BAAPIClient();
export const apiClient = baApiClient;
