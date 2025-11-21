# agents/agent_factory.py
from typing import Dict, List
from .broadcast_agent import BroadcastAgent
from .targeted_agent import TargetedAgent


class AgentFactory:
    """Factory class for creating different types of agents"""

    _agents = {}  # Cache for agent instances

    @staticmethod
    def create_agent(agent_type: str, api_key: str):
        """
        Create or retrieve an agent instance

        Args:
            agent_type: Type of agent ('broadcast' or 'targeted')
            api_key: Anthropic API key

        Returns:
            Agent instance

        Raises:
            ValueError: If agent_type is unknown
        """
        # Return cached agent if exists
        if agent_type in AgentFactory._agents:
            return AgentFactory._agents[agent_type]

        # Create new agent
        if agent_type.lower() == "broadcast":
            agent = BroadcastAgent(api_key)
        elif agent_type.lower() == "targeted":
            agent = TargetedAgent(api_key)
        else:
            raise ValueError(
                f"Unknown agent type: {agent_type}. "
                f"Valid types are: 'broadcast', 'targeted'"
            )

        # Cache the agent
        AgentFactory._agents[agent_type] = agent
        return agent

    @staticmethod
    def get_available_agents() -> List[str]:
        """Get list of available agent types"""
        return ['broadcast', 'targeted']

    @staticmethod
    def clear_cache():
        """Clear the agent cache"""
        AgentFactory._agents = {}

    @staticmethod
    def get_agent_info() -> Dict:
        """Get information about all available agents"""
        return {
            'broadcast': {
                'description': 'Sends alerts to all pharmacies',
                'use_case': 'Critical alerts affecting all locations'
            },
            'targeted': {
                'description': 'Sends alerts to specific pharmacies based on criteria',
                'use_case': 'Location-specific or type-specific alerts'
            }
        }