"""
Business Analyst Agent - Gathers and validates client requirements
Responsibilities:
- Understand client goals and business domain
- Ask clarifying questions
- Extract functional and non-functional requirements
- Identify risks and constraints
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from memory.memory_system import AgentMemory, MemoryType


@dataclass
class RequirementsSummary:
    """Structured summary of all gathered requirements"""
    client_goal: str
    target_users: str
    business_domain: str
    platform_type: str  # web, mobile, both, desktop
    key_features: List[str] = field(default_factory=list)
    constraints: Dict[str, str] = field(default_factory=dict)  # timeline, budget, etc.
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class FunctionalRequirements:
    """Functional requirements for the project"""
    core_features: List[str] = field(default_factory=list)
    user_management: List[str] = field(default_factory=list)
    admin_features: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)
    additional_features: List[str] = field(default_factory=list)


@dataclass
class NonFunctionalRequirements:
    """Performance, security, and scalability requirements"""
    expected_users: str  # "100", "10K", "1M"
    expected_traffic: str  # "low", "medium", "high"
    response_time: str  # "<200ms", "<500ms", etc.
    uptime_sla: str  # "99.9%", "99.5%"
    security_level: str  # "basic", "medium", "high"
    data_storage: str  # "MB", "GB", "TB"
    authentication: str  # "basic", "OAuth", "SSO"
    compliance: List[str] = field(default_factory=list)  # GDPR, HIPAA, etc.
    performance_requirements: Dict[str, str] = field(default_factory=dict)


@dataclass
class RiskAnalysis:
    """Identified risks and mitigation strategies"""
    high_risks: List[Dict[str, str]] = field(default_factory=list)  # {risk, impact, mitigation}
    medium_risks: List[Dict[str, str]] = field(default_factory=list)
    low_risks: List[Dict[str, str]] = field(default_factory=list)
    critical_blockers: List[str] = field(default_factory=list)


class BusinessAnalystAgent:
    """
    Business Analyst Agent - Gathers comprehensive requirements
    Acts as bridge between client needs and technical implementation
    """

    def __init__(self, llm: ChatGroq, memory: Optional[AgentMemory] = None):
        self.llm = llm
        self.memory = memory
        self.message_history = []
        self.system_prompt = SystemMessage(
            content="""You are an expert Business Analyst. Your job is to:
1. Understand client requirements thoroughly
2. Ask clarifying questions
3. Identify hidden requirements and constraints
4. Generate clear, actionable requirement documents

Always be thorough. Ask about:
- Target users and use cases
- Platform requirements (web, mobile, both)
- Performance and scalability needs
- Security and compliance
- Budget and timeline constraints
- Integration requirements
- Admin/management needs

Respond in JSON format with structured data."""
        )
        self.requirements_summary = None
        self.functional_reqs = None
        self.nonfunctional_reqs = None
        self.risk_analysis = None

    async def gather_requirements(
        self, 
        client_goal: str, 
        additional_context: Optional[str] = None
    ) -> List[str]:
        """
        Generate clarifying questions for the client
        Returns list of questions to ask user
        """
        initial_prompt = f"""Client Goal: {client_goal}
Additional Context: {additional_context or "None"}

Generate 10 important clarifying questions I should ask the client:
1. Who are the target users?
2. Is this for Web, Mobile, or Both?
3. Expected user base size?
4. Need authentication/login?
5. Admin dashboard needed?
6. Any integrations (payment, email, SMS)?
7. Timeline and budget constraints?
8. Performance requirements (response time)?
9. Data privacy/compliance needs?
10. Key business metrics/success criteria?

Format response as JSON with:
{{"questions": ["question1", "question2", "question3", ...]}}"""

        self.message_history = [self.system_prompt]
        self.message_history.append(HumanMessage(content=initial_prompt))

        response = await self.llm.ainvoke(self.message_history)
        self.message_history.append(AIMessage(content=response.content))

        # Parse questions from response
        parsed = self._parse_json_response(response.content)
        questions = parsed.get("questions", [
            "Who are the target users?",
            "Is this for Web, Mobile, or Both?",
            "Expected user base (100, 1K, 10K, 1M+)?",
            "Need authentication/login?",
            "Admin dashboard needed?",
            "Any integrations needed?",
            "Timeline constraints?",
            "Budget constraints?",
            "Performance requirements?",
            "Compliance needs (GDPR, HIPAA, PCI-DSS)?"
        ])

        # Store in memory
        if self.memory:
            self.memory.long_term.add(
                content=f"Business Analysis initiated for: {client_goal}",
                tags=["business_analysis", "requirements", "initial"],
                importance=0.95,
                agent="BusinessAnalyst"
            )

        return questions

    async def ask_questions_interactively(
        self,
        client_goal: str
    ) -> Dict[str, str]:
        """
        Ask BA questions to user and collect answers interactively
        Returns dict of answers keyed by question
        """
        # First get the questions
        questions = await self.gather_requirements(client_goal)
        
        print("\n" + "="*70)
        print("💬 BUSINESS ANALYST ASKING QUESTIONS")
        print("="*70 + "\n")
        print(f"Client Goal: {client_goal}\n")
        print("Please answer the following questions naturally.\n")
        
        client_answers = {}
        
        # Ask each question and collect answers
        for i, question in enumerate(questions, 1):
            print(f"Q{i}: {question}")
            answer = input("Your answer: ").strip()
            if answer:
                client_answers[question] = answer
            print()
        
        return client_answers

    async def process_client_answers(
        self, 
        client_answers: Dict[str, str]
    ) -> RequirementsSummary:
        """
        Process client's answers to clarifying questions
        Validates and consolidates into structured requirements
        """
        # Format answers nicely
        formatted_answers = "\n".join([
            f"Q: {q}\nA: {a}\n"
            for q, a in client_answers.items()
        ])
        
        answers_prompt = f"""The client provided these answers to my questions:

{formatted_answers}

Based on these answers, create a comprehensive REQUIREMENTS SUMMARY with:
1. Client Goal (what they want to build)
2. Target Users (who will use it)
3. Business Domain (type of business/application)
4. Platform Type (web/mobile/both/desktop)
5. Key Features needed
6. Timeline and Budget constraints
7. Performance and scalability expectations
8. Security and compliance needs

Format as JSON:
{{
  "client_goal": "...",
  "target_users": "...",
  "business_domain": "...",
  "platform_type": "...",
  "key_features": [...],
  "constraints": {{"timeline": "...", "budget": "...", "other": "..."}},
  "notes": "..."
}}"""

        self.message_history.append(HumanMessage(content=answers_prompt))
        response = await self.llm.ainvoke(self.message_history)
        self.message_history.append(AIMessage(content=response.content))

        parsed = self._parse_json_response(response.content)
        self.requirements_summary = RequirementsSummary(
            client_goal=parsed.get("client_goal", ""),
            target_users=parsed.get("target_users", ""),
            business_domain=parsed.get("business_domain", ""),
            platform_type=parsed.get("platform_type", "web"),
            key_features=parsed.get("key_features", []),
            constraints=parsed.get("constraints", {})
        )

        return self.requirements_summary

    async def extract_functional_requirements(self) -> FunctionalRequirements:
        """
        Extract detailed functional requirements from gathered info
        """
        if not self.requirements_summary:
            raise ValueError("Call process_client_answers() first")

        prompt = f"""Based on the requirements:
{json.dumps(asdict(self.requirements_summary), indent=2)}

Extract and categorize FUNCTIONAL REQUIREMENTS into:
1. Core Features (main functionality)
2. User Management (login, profile, permissions)
3. Admin Features (management, monitoring, reporting)
4. Integrations (payment, email, external APIs)
5. Additional Features (nice-to-have, future)

Format as JSON:
{{
  "core_features": [...],
  "user_management": [...],
  "admin_features": [...],
  "integrations": [...],
  "additional_features": [...]
}}"""

        self.message_history.append(HumanMessage(content=prompt))
        response = await self.llm.ainvoke(self.message_history)
        self.message_history.append(AIMessage(content=response.content))

        parsed = self._parse_json_response(response.content)
        self.functional_reqs = FunctionalRequirements(
            core_features=parsed.get("core_features", []),
            user_management=parsed.get("user_management", []),
            admin_features=parsed.get("admin_features", []),
            integrations=parsed.get("integrations", []),
            additional_features=parsed.get("additional_features", [])
        )

        if self.memory:
            self.memory.long_term.add(
                content=f"Extracted functional requirements: {len(self.functional_reqs.core_features)} core features",
                tags=["functional_requirements", "analysis"],
                importance=0.9,
                agent="BusinessAnalyst"
            )

        return self.functional_reqs

    async def extract_nonfunctional_requirements(self) -> NonFunctionalRequirements:
        """
        Extract performance, security, and scalability requirements
        """
        if not self.requirements_summary:
            raise ValueError("Call process_client_answers() first")

        prompt = f"""Based on the requirements:
{json.dumps(asdict(self.requirements_summary), indent=2)}

Extract NON-FUNCTIONAL REQUIREMENTS:
1. Expected user base (100, 1K, 10K, 1M+)
2. Expected traffic volume (low/medium/high)
3. API response time requirements
4. Uptime SLA (99.9%, 99.5%, etc.)
5. Security level needed (basic/medium/high)
6. Data storage requirements (MB/GB/TB)
7. Authentication method (basic/OAuth/SSO)
8. Compliance needs (GDPR, HIPAA, PCI-DSS, etc.)
9. Performance requirements (caching, CDN, etc.)

Format as JSON:
{{
  "expected_users": "...",
  "expected_traffic": "...",
  "response_time": "...",
  "uptime_sla": "...",
  "security_level": "...",
  "data_storage": "...",
  "authentication": "...",
  "compliance": [...],
  "performance_requirements": {{...}}
}}"""

        self.message_history.append(HumanMessage(content=prompt))
        response = await self.llm.ainvoke(self.message_history)
        self.message_history.append(AIMessage(content=response.content))

        parsed = self._parse_json_response(response.content)
        self.nonfunctional_reqs = NonFunctionalRequirements(
            expected_users=parsed.get("expected_users", "1K"),
            expected_traffic=parsed.get("expected_traffic", "medium"),
            response_time=parsed.get("response_time", "<500ms"),
            uptime_sla=parsed.get("uptime_sla", "99.5%"),
            security_level=parsed.get("security_level", "medium"),
            data_storage=parsed.get("data_storage", "1GB"),
            authentication=parsed.get("authentication", "basic"),
            compliance=parsed.get("compliance", []),
            performance_requirements=parsed.get("performance_requirements", {})
        )

        if self.memory:
            self.memory.long_term.add(
                content=f"Non-functional requirements: {self.nonfunctional_reqs.expected_users} users, {self.nonfunctional_reqs.response_time} response time",
                tags=["nonfunctional_requirements", "performance", "security"],
                importance=0.9,
                agent="BusinessAnalyst"
            )

        return self.nonfunctional_reqs

    async def analyze_risks(self) -> RiskAnalysis:
        """
        Identify and categorize risks based on requirements
        """
        if not self.requirements_summary or not self.functional_reqs:
            raise ValueError("Call process_client_answers() and extract_functional_requirements() first")

        prompt = f"""Analyze risks for this project:

Requirements Summary:
{json.dumps(asdict(self.requirements_summary), indent=2)}

Functional Requirements:
{json.dumps(asdict(self.functional_reqs), indent=2)}

Non-Functional Requirements:
{json.dumps(asdict(self.nonfunctional_reqs), indent=2) if self.nonfunctional_reqs else {}}

Identify and categorize risks:
1. HIGH RISKS (critical, could derail project)
2. MEDIUM RISKS (important, needs mitigation)
3. LOW RISKS (monitor but manageable)
4. CRITICAL BLOCKERS (deal-breakers)

For each risk, provide:
- Risk description
- Potential impact
- Mitigation strategy
- Severity level

Format as JSON:
{{
  "high_risks": [{{"risk": "...", "impact": "...", "mitigation": "..."}}],
  "medium_risks": [{{"risk": "...", "impact": "...", "mitigation": "..."}}],
  "low_risks": [{{"risk": "...", "impact": "...", "mitigation": "..."}}],
  "critical_blockers": ["blocker1", "blocker2"]
}}"""

        self.message_history.append(HumanMessage(content=prompt))
        response = await self.llm.ainvoke(self.message_history)
        self.message_history.append(AIMessage(content=response.content))

        parsed = self._parse_json_response(response.content)
        self.risk_analysis = RiskAnalysis(
            high_risks=parsed.get("high_risks", []),
            medium_risks=parsed.get("medium_risks", []),
            low_risks=parsed.get("low_risks", []),
            critical_blockers=parsed.get("critical_blockers", [])
        )

        if self.memory:
            total_risks = len(self.risk_analysis.high_risks) + len(self.risk_analysis.medium_risks)
            self.memory.long_term.add(
                content=f"Risk analysis complete: {len(self.risk_analysis.high_risks)} high, {len(self.risk_analysis.medium_risks)} medium risks",
                tags=["risk_analysis", "mitigation"],
                importance=0.95,
                agent="BusinessAnalyst"
            )

        return self.risk_analysis

    async def generate_complete_requirements_doc(self) -> Dict[str, Any]:
        """
        Generate complete requirements document combining all analyses
        """
        return {
            "summary": asdict(self.requirements_summary) if self.requirements_summary else {},
            "functional_requirements": asdict(self.functional_reqs) if self.functional_reqs else {},
            "nonfunctional_requirements": asdict(self.nonfunctional_reqs) if self.nonfunctional_reqs else {},
            "risk_analysis": asdict(self.risk_analysis) if self.risk_analysis else {},
            "generated_at": datetime.now().isoformat()
        }

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract and parse JSON from LLM response
        Handles various JSON formatting quirks
        """
        try:
            # Try direct JSON parse
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting from ```json blocks
        if "```json" in response_text:
            try:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                pass

        # Try extracting from {} blocks
        if "{" in response_text and "}" in response_text:
            try:
                start = response_text.rfind("{")
                end = response_text.rfind("}") + 1
                if start < end:
                    json_str = response_text[start:end]
                    # Clean trailing commas
                    json_str = json_str.replace(",\n}", "\n}").replace(",\n]", "\n]")
                    return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Return empty dict if all parsing fails
        print(f"Warning: Could not parse JSON from response: {response_text[:100]}")
        return {}
