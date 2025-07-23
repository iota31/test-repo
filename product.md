# Product Overview

## Incident Agent - MCP-Powered DevOps Automation

An AI-powered DevOps automation system that uses MCP (Model Context Protocol) agents to detect, diagnose, fix, and deploy hotfixes for production issues automatically.

### Core Functionality

- **Automated Issue Detection**: Continuously monitors logs for anomalies and production issues
- **Intelligent Bug Classification**: Deduplicates and enriches issue reports with contextual information
- **AI-Powered Fix Generation**: Uses specialized AI agents to investigate issues and generate fixes
- **Automated Testing & Deployment**: Integrates with CI/CD pipelines for testing and deploying hotfixes

### Multi-Agent Architecture

The system implements a cooperative multi-agent architecture:

1. **Monitoring Service**: Detects anomalies in logs and system metrics
2. **Bug Classifier**: Categorizes and deduplicates issues, prevents duplicate work
3. **CustomFixWorker**: Core AI agent that investigates issues and generates fixes using MCP tools
4. **Agent Spawner**: Orchestrates agent workflows and manages containerized execution
5. **Shared Context**: Provides centralized state management across all services

### Key Integrations

- **GitHub**: Version control, issue tracking, and pull request management via MCP server
- **Jenkins**: CI/CD pipeline integration for automated testing via MCP server
- **Code Search**: Semantic code retrieval and analysis via custom MCP server
- **Shell Tools**: Command execution capabilities via MCP server
- **LLM Providers**: OpenAI, Anthropic, and OpenRouter for AI reasoning

### Target Use Cases

- Production incident response automation
- Hotfix generation and deployment
- Log anomaly detection and alerting
- Automated bug triage and classification
- DevOps workflow automation