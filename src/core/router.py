"""
Smart Routing Logic for Support Queries.

Routes queries based on classification results, priority, and multi-intent detection.
"""

from typing import List, Dict, Optional
from enum import Enum

from src.core.models import ClassificationResult, SupportCategory
from src.utils.logger import get_logger

logger = get_logger()


# ============================================================================
# ROUTING MODELS
# ============================================================================

class RoutingDestination(str, Enum):
    """Where to route the query."""
    AUTO_RESPONSE = "auto_response"  # Automated response (FAQ, chatbot)
    TIER_1_SUPPORT = "tier_1_support"  # Junior support agent
    TIER_2_SUPPORT = "tier_2_support"  # Senior support agent
    SPECIALIST_BILLING = "specialist_billing"  # Billing specialist
    SPECIALIST_TECHNICAL = "specialist_technical"  # Technical specialist
    ESCALATION_TEAM = "escalation_team"  # Manager/Escalation team
    MULTI_INTENT_TRIAGE = "multi_intent_triage"  # Special queue for multi-intent


class RoutingAction(str, Enum):
    """What action to take."""
    SINGLE_TICKET = "single_ticket"  # Create one ticket
    SPLIT_TICKETS = "split_tickets"  # Split into multiple tickets
    ESCALATE_IMMEDIATELY = "escalate_immediately"  # Urgent escalation
    QUEUE_NORMAL = "queue_normal"  # Add to normal queue
    QUEUE_PRIORITY = "queue_priority"  # Priority queue


class RoutingDecision:
    """Complete routing decision for a query."""
    
    def __init__(
        self,
        destination: RoutingDestination,
        action: RoutingAction,
        priority: str,
        estimated_wait_time: str,
        reasoning: str,
        requires_split: bool = False,
        split_categories: Optional[List[SupportCategory]] = None,
        special_instructions: Optional[str] = None
    ):
        self.destination = destination
        self.action = action
        self.priority = priority
        self.estimated_wait_time = estimated_wait_time
        self.reasoning = reasoning
        self.requires_split = requires_split
        self.split_categories = split_categories or []
        self.special_instructions = special_instructions


# ============================================================================
# SMART ROUTER
# ============================================================================

class SmartRouter:
    """
    Intelligent query routing based on classification results.
    
    Routes queries to appropriate teams/queues based on:
    - Primary category
    - Confidence level
    - Multi-intent detection
    - Priority level
    - Human review requirements
    """
    
    def __init__(self):
        """Initialize smart router with routing rules."""
        logger.debug("SmartRouter initialized")
    
    def route(self, result: ClassificationResult) -> RoutingDecision:
        """
        Determine routing for a classified query.
        
        Args:
            result: Classification result
            
        Returns:
            RoutingDecision with destination and action
        """
        logger.info(
            "Routing query",
            category=result.category.value,
            confidence=result.confidence,
            is_multi_intent=result.is_multi_intent,
            priority=result.routing_priority
        )
        
        # Handle multi-intent queries specially
        if result.is_multi_intent:
            return self._route_multi_intent(result)
        
        # Handle by priority
        if result.routing_priority == "critical":
            return self._route_critical(result)
        
        # Handle low confidence queries
        if result.confidence < 0.5:
            return self._route_low_confidence(result)
        
        # Handle by category
        return self._route_by_category(result)
    
    def _route_multi_intent(self, result: ClassificationResult) -> RoutingDecision:
        """Route multi-intent queries."""
        
        # Count number of intents
        intent_count = 1 + len(result.additional_categories)
        
        # If 2 intents and one is simple, might auto-handle
        if intent_count == 2 and result.confidence >= 0.7:
            return RoutingDecision(
                destination=RoutingDestination.TIER_2_SUPPORT,
                action=RoutingAction.SINGLE_TICKET,
                priority=result.routing_priority,
                estimated_wait_time="5-15 minutes",
                reasoning=(
                    f"Multi-intent query ({result.category.value} + "
                    f"{result.additional_categories[0].value}). "
                    "Routing to senior agent for comprehensive handling."
                ),
                requires_split=False,
                special_instructions=(
                    f"Query contains multiple issues: {result.category.value} "
                    f"and {', '.join(c.value for c in result.additional_categories)}. "
                    "Address all concerns in response."
                )
            )
        
        # 3+ intents or complex cases → split tickets
        return RoutingDecision(
            destination=RoutingDestination.MULTI_INTENT_TRIAGE,
            action=RoutingAction.SPLIT_TICKETS,
            priority="high",
            estimated_wait_time="Immediate triage",
            reasoning=(
                f"Complex multi-intent query with {intent_count} distinct issues. "
                "Recommend splitting into separate tickets for specialized handling."
            ),
            requires_split=True,
            split_categories=[result.category] + result.additional_categories,
            special_instructions=(
                "Split this query into separate tickets:\n" +
                "\n".join([
                    f"• {cat.value}" 
                    for cat in [result.category] + result.additional_categories
                ]) +
                "\n\nEnsure all tickets are linked for context."
            )
        )
    
    def _route_critical(self, result: ClassificationResult) -> RoutingDecision:
        """Route critical priority queries."""
        
        return RoutingDecision(
            destination=RoutingDestination.ESCALATION_TEAM,
            action=RoutingAction.ESCALATE_IMMEDIATELY,
            priority="critical",
            estimated_wait_time="Immediate",
            reasoning=(
                f"Critical issue detected in {result.category.value}. "
                "Immediate escalation required."
            ),
            special_instructions="Alert on-call manager. Immediate response required."
        )
    
    def _route_low_confidence(self, result: ClassificationResult) -> RoutingDecision:
        """Route low confidence classifications."""
        
        return RoutingDecision(
            destination=RoutingDestination.TIER_1_SUPPORT,
            action=RoutingAction.QUEUE_NORMAL,
            priority=result.routing_priority,
            estimated_wait_time="15-30 minutes",
            reasoning=(
                f"Low confidence classification ({result.confidence:.0%}). "
                "Human agent will assess and recategorize if needed."
            ),
            special_instructions=(
                f"AI classified as {result.category.value} with low confidence. "
                "Please verify category and recategorize if needed."
            )
        )
    
    def _route_by_category(self, result: ClassificationResult) -> RoutingDecision:
        """Route based on category with high confidence."""
        
        routing_map = {
            SupportCategory.BILLING: (
                RoutingDestination.SPECIALIST_BILLING,
                "10-20 minutes",
                "Billing specialist for payment issues"
            ),
            SupportCategory.TECHNICAL: (
                RoutingDestination.SPECIALIST_TECHNICAL,
                "15-25 minutes",
                "Technical specialist for troubleshooting"
            ),
            SupportCategory.ACCOUNT: (
                RoutingDestination.TIER_1_SUPPORT,
                "5-10 minutes",
                "Tier 1 support for account management"
            ),
            SupportCategory.FEATURE: (
                RoutingDestination.TIER_2_SUPPORT,
                "1-2 hours",
                "Product team for feature request evaluation"
            ),
            SupportCategory.BUG: (
                RoutingDestination.SPECIALIST_TECHNICAL,
                "20-30 minutes",
                "Technical team for bug investigation"
            ),
            SupportCategory.PRODUCT: (
                RoutingDestination.TIER_1_SUPPORT,
                "5-15 minutes",
                "General support for product questions"
            ),
            SupportCategory.GENERAL: (
                RoutingDestination.AUTO_RESPONSE,
                "Immediate",
                "Automated FAQ response system"
            ),
        }
        
        destination, wait_time, reason = routing_map.get(
            result.category,
            (RoutingDestination.TIER_1_SUPPORT, "10-20 minutes", "General support queue")
        )
        
        # High priority queries go to priority queue
        action = (
            RoutingAction.QUEUE_PRIORITY 
            if result.routing_priority in ["critical", "high"]
            else RoutingAction.QUEUE_NORMAL
        )
        
        return RoutingDecision(
            destination=destination,
            action=action,
            priority=result.routing_priority,
            estimated_wait_time=wait_time,
            reasoning=f"{reason}. Confidence: {result.confidence:.0%}"
        )


# ============================================================================
# SINGLETON
# ============================================================================

_router_instance = None

def get_router() -> SmartRouter:
    """Get router singleton."""
    global _router_instance
    if _router_instance is None:
        _router_instance = SmartRouter()
    return _router_instance
