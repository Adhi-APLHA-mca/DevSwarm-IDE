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
   * Receives Q&A context from Business Analyst for informed decision-making
   */
  async generateDevelopmentPlan(
    requirements: any, 
    projectGoal: string,
    questions?: string[],
    answers?: { [key: number]: string }
  ): Promise<string> {
    try {
      const apiKey = import.meta.env.REACT_APP_GROQ_API_KEY;

      // Format Q&A history for context
      const qaContext = questions && answers 
        ? questions.map((q, idx) => `Q${idx + 1}: ${q}\nA: ${answers[idx] || 'Not answered'}`).join('\n\n')
        : 'No Q&A history available';

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
                content: `You are an experienced Chief Executive Officer and Strategic Project Manager with expertise in software development. Your role is to create a COMPREHENSIVE, DETAILED, and PROFESSIONAL development plan from requirements gathered by the Business Analyst.

Format the plan with these sections:
1. **Executive Summary** - Overview of project scope, objectives, and expected outcomes (2-3 sentences)
2. **Project Objectives** - Key success criteria and deliverables
3. **Scope of Work** - What is included and excluded from the project
4. **Development Phases** - Detailed phases with specific milestones and timelines:
   - For each phase include: Duration, Key Activities, Deliverables, Success Criteria
5. **Technical Architecture** - High-level technology stack and architecture decisions
6. **Resource Requirements** - Team composition, skills needed, estimated effort
7. **Risk Assessment** - Identify 3-4 key risks and mitigation strategies
8. **Quality Assurance Strategy** - Testing approach and quality standards
9. **Timeline & Milestones** - Overall project timeline with key dates
10. **Success Metrics** - How project success will be measured
11. **Post-Launch Support** - Maintenance and enhancement strategy

Use professional language, be specific with numbers and estimates where possible, and provide actionable guidance. Output in professional markdown format with clear hierarchy.`,
              },
              {
                role: "user",
                content: `PROJECT GOAL: "${projectGoal}"

BUSINESS ANALYST REQUIREMENTS GATHERING CONTEXT:

${qaContext}

PROCESSED REQUIREMENTS SUMMARY:
${JSON.stringify(requirements, null, 2)}

Your task:
1. Review the questions asked by the Business Analyst and the customer's answers
2. Analyze the processed requirements
3. Create a DETAILED, COMPREHENSIVE development plan suitable for presenting to stakeholders
4. Include specific timelines (phases with weeks), resource estimates, risk mitigation strategies, and success metrics
5. Reference insights from the Q&A process to demonstrate understanding of customer needs
6. Allocate work across different specialized agents (Code Writers, Reviewers, Debuggers, etc.)

Format the output as a professional strategic development plan in markdown.`,
              },
            ],
            temperature: 0.7,
            max_tokens: 3500,
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

    // Fallback: Comprehensive professional plan template
    return `# Strategic Development Plan
## ${projectGoal}

---

## Executive Summary

This comprehensive development plan outlines the strategic approach, resource allocation, and timeline for delivering a robust, scalable solution that meets all identified stakeholder requirements. The project will be executed in four distinct phases, with each phase building upon the previous deliverables to ensure quality and risk mitigation.

---

## Project Objectives

- Deliver a fully functional, production-ready solution within the planned timeline
- Ensure seamless integration with existing systems and workflows
- Achieve high user adoption rates through intuitive design and comprehensive training
- Maintain 99.5% system uptime and ensure data security compliance
- Enable future scalability and feature enhancements

---

## Scope of Work

**Included:**
- Requirements analysis and architecture design
- Full feature development and implementation
- Comprehensive testing (unit, integration, UAT)
- Deployment to production environment
- User documentation and training materials
- Post-launch support for 90 days

**Excluded:**
- Legacy system migration (to be handled separately)
- Third-party vendor integrations beyond scope
- Unlimited custom feature requests post-launch

---

## Development Phases

### Phase 1: Planning & Architecture (Weeks 1-3)
- **Duration:** 3 weeks
- **Key Activities:** Requirements finalization, system architecture design, technology stack selection, infrastructure planning
- **Deliverables:** Architecture document, technical specifications, project roadmap, development environment setup
- **Success Criteria:** Approved architecture, clear development guidelines, environment ready
- **Team:** 2 architects, 1 PM, 1 BA

### Phase 2: Core Development (Weeks 4-12)
- **Duration:** 9 weeks
- **Key Activities:** Backend API development, frontend implementation, database design, integration testing
- **Deliverables:** Functional core features, API documentation, unit test coverage >80%
- **Success Criteria:** All core features complete, code review passed, no critical bugs
- **Team:** 4-5 developers, 1 tech lead, 1 QA

### Phase 3: Testing & Optimization (Weeks 13-16)
- **Duration:** 4 weeks
- **Key Activities:** User acceptance testing, performance optimization, security audit, bug fixes
- **Deliverables:** Test report, performance benchmarks, security audit results, optimized codebase
- **Success Criteria:** UAT passed, <5 critical issues, performance targets met
- **Team:** 2 QA engineers, 2 developers, 1 security expert

### Phase 4: Deployment & Launch (Weeks 17-20)
- **Duration:** 4 weeks
- **Key Activities:** Production deployment, user training, go-live support, monitoring setup
- **Deliverables:** Deployed system, user training materials, operational documentation, monitoring dashboards
- **Success Criteria:** Smooth go-live, <1% critical incidents, 100% monitoring coverage
- **Team:** 1 DevOps engineer, 2 support engineers, 1 PM

---

## Technical Architecture

- **Frontend:** Modern responsive web application (React, TypeScript, responsive design)
- **Backend:** Scalable API layer (RESTful/GraphQL architecture)
- **Database:** Relational database with proper indexing and backup strategy
- **Infrastructure:** Cloud-based deployment with auto-scaling capabilities
- **Security:** End-to-end encryption, secure authentication, GDPR compliance

---

## Resource Requirements

**Total Team Size:** 10-12 core team members

**Composition:**
- 1 Project Manager
- 1 Solution Architect
- 5 Full-Stack Developers
- 2 Quality Assurance Engineers
- 1 DevOps/Infrastructure Engineer
- 1 Technical Writer/Documentation Specialist

**Skills Required:**
- Full-stack web development
- Database design and optimization
- API development
- Cloud infrastructure (AWS/Azure/GCP)
- Security best practices

---

## Risk Assessment & Mitigation

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|-------------------|
| Scope Creep | Schedule delay, budget overrun | Medium | Strict change control, requirement freeze after phase 1 |
| Resource Availability | Timeline delay | Low | Backup team members identified, cross-training planned |
| Technical Challenges | Quality issues, rework | Medium | Regular architecture reviews, spike solutions for unknowns |
| Integration Issues | Deployment delays | Medium | Early integration testing, vendor coordination meetings |

---

## Quality Assurance Strategy

- **Unit Testing:** Minimum 80% code coverage
- **Integration Testing:** End-to-end workflow validation
- **Performance Testing:** Load testing at 150% expected capacity
- **Security Testing:** Penetration testing, vulnerability scanning
- **User Acceptance Testing:** Real user scenarios with stakeholder validation

---

## Timeline & Key Milestones

| Milestone | Target Date | Deliverable |
|-----------|------------|-------------|
| Architecture Approval | End of Week 3 | Approved technical design |
| Alpha Release | End of Week 12 | Feature-complete build for testing |
| Beta Release | End of Week 16 | Production-ready release candidate |
| Production Go-Live | End of Week 20 | Live system with full support |
| Post-Launch Stabilization | End of Week 24 | Handoff to operations team |

---

## Success Metrics

- **Delivery:** On-time delivery within budget
- **Quality:** <1% critical defects in production within 30 days post-launch
- **Performance:** API response time <500ms, system uptime 99.5%+
- **User Adoption:** 95%+ of target users active within 60 days
- **Satisfaction:** User satisfaction score >4.5/5.0
- **ROI:** Measurable business impact within 90 days of launch

---

## Post-Launch Support & Maintenance

- **30-Day Support:** Full development team on-call for critical issues
- **90-Day Support:** Maintenance phase with bug fixes and minor enhancements
- **Ongoing:** Transition to maintenance team with 1 dedicated resource
- **Future Enhancements:** Quarterly review of feature requests and optimization opportunities

---

**Prepared by:** CEO/Orchestrator Agent  
**Date:** ${new Date().toLocaleDateString()}  
**Project Status:** Approved for Execution`;
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
