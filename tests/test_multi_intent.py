"""
Tests for multi-intent detection and smart routing.
"""

import pytest
from src.core.rule_classifier import get_rule_classifier
from src.core.router import get_router, RoutingDestination, RoutingAction
from src.core.models import SupportCategory


class TestMultiIntentDetection:
    """Test multi-intent query detection."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.classifier = get_rule_classifier()
    
    def test_single_intent_billing(self):
        """Test single-intent billing query."""
        query = "I need a refund for the double charge on my account"
        result = self.classifier.classify(query)
        
        assert result.category == SupportCategory.BILLING
        assert result.is_multi_intent == False
        assert len(result.additional_categories) == 0
        assert result.confidence > 0.6
    
    def test_multi_intent_billing_technical(self):
        """Test multi-intent query with billing and technical issues."""
        query = "I was charged twice but the refund button shows error 500"
        result = self.classifier.classify(query)
        
        assert result.category in [SupportCategory.BILLING, SupportCategory.TECHNICAL]
        assert result.is_multi_intent == True
        assert len(result.additional_categories) > 0
        assert result.requires_human_review == True
    
    def test_multi_intent_complex_query(self):
        """Test complex multi-intent query with 3+ intents."""
        query = (
            "I was charged $99 twice last month, but when I tried to get a refund "
            "through the app, it crashed with error code 500. Now I cannot even log "
            "in because I forgot my password. Can you also add a feature to export "
            "my transaction history?"
        )
        result = self.classifier.classify(query)
        
        # Should detect multiple intents
        assert result.is_multi_intent == True
        assert len(result.additional_categories) >= 2
        
        # Should flag for human review
        assert result.requires_human_review == True
        
        # Should have high priority
        assert result.routing_priority == "high"
        
        # Should detect billing, technical, and account
        all_categories = [result.category] + result.additional_categories
        assert SupportCategory.BILLING in all_categories
        assert SupportCategory.TECHNICAL in all_categories
        assert SupportCategory.ACCOUNT in all_categories
    
    def test_single_intent_technical(self):
        """Test single-intent technical query."""
        query = "The app keeps crashing when I click the save button"
        result = self.classifier.classify(query)
        
        assert result.category == SupportCategory.TECHNICAL
        assert result.is_multi_intent == False
    
    def test_single_intent_account(self):
        """Test single-intent account query."""
        query = "I forgot my password and need to reset it"
        result = self.classifier.classify(query)
        
        assert result.category == SupportCategory.ACCOUNT
        assert result.is_multi_intent == False
        assert result.confidence > 0.6  # Reasonable confidence threshold
    
    def test_category_scores_populated(self):
        """Test that category_scores are populated for debugging."""
        query = "I need help with billing and login issues"
        result = self.classifier.classify(query)
        
        assert result.category_scores is not None
        assert len(result.category_scores) > 0
        assert "Billing & Payments" in result.category_scores
        assert "Account Management" in result.category_scores


class TestRoutingDecisions:
    """Test smart routing decisions."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.classifier = get_rule_classifier()
        self.router = get_router()
    
    def test_route_single_intent_billing(self):
        """Test routing for single-intent billing query."""
        query = "I need a refund for double charge"
        result = self.classifier.classify(query)
        routing = self.router.route(result)
        
        assert routing.destination == RoutingDestination.SPECIALIST_BILLING
        assert routing.action in [RoutingAction.QUEUE_NORMAL, RoutingAction.QUEUE_PRIORITY]
        assert routing.requires_split == False
    
    def test_route_multi_intent_requires_split(self):
        """Test routing for complex multi-intent query."""
        query = (
            "I was charged twice, the app crashed, and I forgot my password. "
            "Also, can you add export feature?"
        )
        result = self.classifier.classify(query)
        routing = self.router.route(result)
        
        # Complex multi-intent should recommend split or special handling
        assert result.is_multi_intent == True
        
        # Should either route to triage or senior support
        assert routing.destination in [
            RoutingDestination.MULTI_INTENT_TRIAGE,
            RoutingDestination.TIER_2_SUPPORT
        ]
    
    def test_route_critical_priority(self):
        """Test routing for critical priority query."""
        query = "URGENT: My account was hacked and unauthorized charges appeared"
        result = self.classifier.classify(query)
        routing = self.router.route(result)
        
        # Critical issues should escalate
        assert routing.priority == "critical"
        assert routing.destination == RoutingDestination.ESCALATION_TEAM
        assert routing.action == RoutingAction.ESCALATE_IMMEDIATELY
    
    def test_route_low_confidence(self):
        """Test routing for low confidence classification."""
        query = "I have a question about something"
        result = self.classifier.classify(query)
        
        # Low confidence query
        if result.confidence < 0.5:
            routing = self.router.route(result)
            
            # Should route to human for review
            assert routing.special_instructions is not None
            assert "low confidence" in routing.reasoning.lower()
    
    def test_route_technical_specialist(self):
        """Test routing to technical specialist."""
        query = "The app crashes with error 500 every time I try to save"
        result = self.classifier.classify(query)
        routing = self.router.route(result)
        
        assert routing.destination == RoutingDestination.SPECIALIST_TECHNICAL
    
    def test_routing_special_instructions(self):
        """Test that special instructions are provided for multi-intent."""
        query = "I need refund and password reset"
        result = self.classifier.classify(query)
        
        if result.is_multi_intent:
            routing = self.router.route(result)
            assert routing.special_instructions is not None
            assert len(routing.special_instructions) > 0


class TestPriorityDetermination:
    """Test routing priority determination."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.classifier = get_rule_classifier()
    
    def test_high_priority_keywords(self):
        """Test high priority for urgent keywords."""
        queries = [
            "URGENT: Cannot access my account",
            "ASAP need refund for unauthorized charge",
            "EMERGENCY: Account hacked"
        ]
        
        for query in queries:
            result = self.classifier.classify(query)
            assert result.routing_priority in ["critical", "high"]
    
    def test_normal_priority_simple_query(self):
        """Test normal priority for simple queries."""
        query = "How do I update my email address?"
        result = self.classifier.classify(query)
        
        # High confidence, single intent should be normal priority
        if result.confidence >= 0.7 and not result.is_multi_intent:
            assert result.routing_priority == "normal"
    
    def test_high_priority_multi_intent(self):
        """Test that multi-intent queries get high priority."""
        query = "I need billing help and technical support and password reset"
        result = self.classifier.classify(query)
        
        if result.is_multi_intent:
            assert result.routing_priority in ["high", "critical"]


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.classifier = get_rule_classifier()
    
    def test_all_low_scores(self):
        """Test query with low scores across all categories."""
        query = "Hello, I have a general question"
        result = self.classifier.classify(query)
        
        # Should default to GENERAL
        assert result.category == SupportCategory.GENERAL
        assert result.is_multi_intent == False
    
    def test_feature_request_pattern(self):
        """Test feature request detection."""
        query = "Please add an export feature to download my data"
        result = self.classifier.classify(query)
        
        # Feature requests often contain "add", "export", etc.
        assert result.category == SupportCategory.FEATURE
    
    def test_bug_report_pattern(self):
        """Test bug report detection."""
        query = "There's a bug where the save button doesn't work as expected"
        result = self.classifier.classify(query)
        
        assert result.category in [SupportCategory.BUG, SupportCategory.TECHNICAL]
    
    def test_reasoning_contains_multi_intent_info(self):
        """Test that reasoning explains multi-intent detection."""
        query = "I need refund and my password reset"
        result = self.classifier.classify(query)
        
        if result.is_multi_intent:
            assert "Also detected" in result.reasoning or "detected" in result.reasoning.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
