# Agents

The agent layer is deliberately lightweight and framework-independent.

Agents:

- Property Matching Agent
- Applicant Intelligence Agent
- RAG Agent
- Next Best Action Agent

Agents return typed `AgentResult` objects. The orchestrator controls execution and agents do not call each other arbitrarily. Matching, applicant intelligence and RAG run in parallel; the action agent runs after those results are available.

