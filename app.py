"""
QnA Support Application - Streamlit UI

Main application interface for support query classification.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from src.core.config import get_settings
from src.core.models import QueryInput, SessionMetrics
from src.core.classifier import get_classifier
from src.core.router import get_router
from src.utils.logger import setup_logger, get_logger
from pydantic import ValidationError

# Initialize logging
setup_logger()
logger = get_logger()

# Page configuration
st.set_page_config(
    page_title="QnA Support Application",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize
settings = get_settings()
classifier = get_classifier()
router = get_router()

# Session state initialization
if 'classifications' not in st.session_state:
    st.session_state.classifications = []

if 'session_id' not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

logger.info("Streamlit app initialized", session_id=st.session_state.session_id)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def classify_query(query_text: str, user_id: str = None):
    """Classify a query and store result."""
    try:
        # Create QueryInput
        query = QueryInput(
            query_text=query_text,
            user_id=user_id,
            session_id=st.session_state.session_id
        )
        
        # Classify
        with st.spinner("🔄 Classifying query..."):
            result = classifier.classify(query)
        
        # Store in session
        result_dict = result.model_dump()
        result_dict['query_text'] = query_text
        result_dict['timestamp'] = datetime.now().isoformat()
        st.session_state.classifications.append(result_dict)
        
        logger.info(
            "Query classified via UI",
            category=result.category.value,
            confidence=result.confidence,
            method=result.method.value
        )
        
        return result
        
    except ValidationError as e:
        st.error(f"❌ Invalid input: {e.errors()[0]['msg']}")
        logger.error(f"Validation error: {e}")
        return None
    
    except Exception as e:
        st.error(f"❌ Classification failed: {str(e)}")
        logger.error(f"Classification error: {e}")
        return None


def calculate_session_metrics() -> SessionMetrics:
    """Calculate metrics from session classifications."""
    if not st.session_state.classifications:
        return SessionMetrics()
    
    df = pd.DataFrame(st.session_state.classifications)
    
    metrics = SessionMetrics(
        total_queries=len(df),
        rule_based_count=len(df[df['method'] == 'rule-based']),
        llm_fallback_count=len(df[df['method'] == 'llm-fallback']),
        average_confidence=df['confidence'].mean(),
        average_response_time_ms=df['response_time_ms'].mean(),
        total_tokens_used=df['llm_tokens_used'].fillna(0).sum(),
        estimated_total_cost=df['estimated_cost'].fillna(0).sum(),
        category_distribution=df['category'].value_counts().to_dict()
    )
    
    return metrics


# ============================================================================
# UI LAYOUT
# ============================================================================

# Header
st.title("🎫 QnA Support Application")
st.markdown("**Intelligent Support Query Classification System**")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📊 Configuration")
    
    st.metric("Confidence Threshold", f"{settings.confidence_threshold:.0%}")
    st.metric("LLM Model", settings.azure_openai_model_name)
    st.metric("Session ID", st.session_state.session_id[:8] + "...")
    
    st.markdown("---")
    
    st.header("📚 Categories")
    categories = [
        "Billing & Payments",
        "Technical Issues",
        "Account Management",
        "Product Questions",
        "Feature Requests",
        "Bug Reports",
        "General Inquiry"
    ]
    for cat in categories:
        st.markdown(f"• {cat}")
    
    st.markdown("---")
    
    st.header("🧪 Sample Queries")
    sample_queries = [
        "I was charged twice for my subscription",
        "The app crashes when I upload files",
        "I forgot my password and can't log in",
        "How do I export my data to CSV?",
        "Please add dark mode to the app",
        "The total amount shown is incorrect"
    ]
    
    for sample in sample_queries:
        if st.button(sample, key=f"sample_{hash(sample)}", width="stretch"):
            st.session_state.current_query = sample

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Enter Support Query")
    
    # Use a form to properly capture input and button click together
    with st.form(key="query_form", clear_on_submit=False):
        # Get query from sample button or text input
        default_query = st.session_state.get('current_query', '')
        
        query_input = st.text_area(
            "Customer Query",
            value=default_query,
            placeholder="e.g., I was charged twice for my subscription this month...",
            height=150,
            help="Enter the customer's support query to classify",
            key="query_text_input"
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            classify_btn = st.form_submit_button(
                "🔍 Classify Query",
                type="primary",
                width="stretch"
            )
        
        with col_btn2:
            clear_btn = st.form_submit_button(
                "🗑️ Clear",
                width="stretch"
            )
    
    # Reset button outside the form (separate action)
    reset_btn = st.button(
        "🔄 Reset Session",
        width="stretch",
        key="reset_session_btn"
    )
    
    # Clear the sample query after form submission
    if classify_btn and 'current_query' in st.session_state:
        del st.session_state.current_query

with col2:
    st.subheader("⚙️ System Status")
    
    if st.session_state.classifications:
        metrics = calculate_session_metrics()
        
        # Show last query info
        last_query = st.session_state.classifications[-1]
        st.info(f"**Last Query**: {last_query['query_text'][:50]}...")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Category", last_query['category'])
        with col_s2:
            confidence_pct = f"{last_query['confidence']:.0%}"
            st.metric("Confidence", confidence_pct)
        
        st.markdown("---")
        
        # Session metrics
        st.metric("Total Queries", metrics.total_queries)
        st.metric("Avg Confidence", f"{metrics.average_confidence:.0%}")
        st.metric(
            "Rule-Based %",
            f"{metrics.rule_based_percentage():.0f}%"
        )
    else:
        st.info("No queries classified yet")

# Classification Logic
if classify_btn:
    logger.info(f"Classify button clicked | query_length={len(query_input) if query_input else 0}")
    
    if not query_input or not query_input.strip():
        st.warning("⚠️ Please enter a query to classify")
        logger.warning("Empty query submitted")
    elif len(query_input.strip()) < 5:
        st.warning("⚠️ Query must be at least 5 characters long")
        logger.warning(f"Query too short: {len(query_input.strip())} chars")
    else:
        result = classify_query(query_input)
        
        if result:
            st.markdown("---")
            st.subheader("📊 Classification Results")
            
            # Multi-intent warning banner
            if result.is_multi_intent:
                st.warning(
                    f"⚠️ **Multi-Intent Query Detected!** "
                    f"This query contains multiple issues that may need separate handling."
                )
            
            # Human review flag
            if result.requires_human_review:
                st.error(
                    f"🚨 **Human Review Required** | Priority: {result.routing_priority.upper()}"
                )
            
            # Main metrics
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            
            with col_r1:
                st.metric("**Primary Category**", result.category.value)
            
            with col_r2:
                confidence_color = "🟢" if result.confidence >= 0.7 else "🟡" if result.confidence >= 0.5 else "🔴"
                st.metric("**Confidence**", f"{confidence_color} {result.confidence:.0%}")
            
            with col_r3:
                method_emoji = "⚡" if result.method.value == "rule-based" else "🤖"
                st.metric("**Method**", f"{method_emoji} {result.method.value.replace('-', ' ').title()}")
            
            with col_r4:
                priority_emoji = {"critical": "🔴", "high": "🟡", "normal": "🟢", "low": "⚪"}.get(result.routing_priority, "🟢")
                st.metric("**Priority**", f"{priority_emoji} {result.routing_priority.title()}")
            
            # Additional categories if multi-intent
            if result.additional_categories:
                st.markdown("**Additional Intents Detected:**")
                cols = st.columns(len(result.additional_categories))
                for idx, cat in enumerate(result.additional_categories):
                    with cols[idx]:
                        cat_score = result.category_scores.get(cat.value, 0) if result.category_scores else 0
                        st.info(f"**{cat.value}**\n\n{cat_score:.0%} confidence")
            
            # Reasoning
            st.info(f"💡 **Reasoning**: {result.reasoning}")
            
            # Confidence visualization
            st.progress(result.confidence)
            
            # Additional details
            if result.llm_tokens_used:
                with st.expander("🔍 LLM Details"):
                    col_llm1, col_llm2 = st.columns(2)
                    with col_llm1:
                        st.metric("Tokens Used", result.llm_tokens_used)
                    with col_llm2:
                        st.metric("Estimated Cost", f"${result.estimated_cost:.6f}")
            
            # Show all category scores in debug mode
            if result.category_scores:
                with st.expander("🔍 All Category Scores (Debug)"):
                    scores_df = pd.DataFrame([
                        {"Category": cat, "Confidence": f"{score:.2%}"}
                        for cat, score in sorted(
                            result.category_scores.items(),
                            key=lambda x: x[1],
                            reverse=True
                        )
                    ])
                    st.dataframe(scores_df, use_container_width=True, hide_index=True)
            
            # Smart Routing Decision
            st.markdown("---")
            st.subheader("🎯 Routing Decision")
            
            routing = router.route(result)
            
            col_route1, col_route2 = st.columns(2)
            with col_route1:
                st.info(f"**Destination**: {routing.destination.value.replace('_', ' ').title()}")
                st.info(f"**Action**: {routing.action.value.replace('_', ' ').title()}")
            
            with col_route2:
                st.info(f"**Est. Wait Time**: {routing.estimated_wait_time}")
                if routing.requires_split:
                    st.warning("**⚠️ Ticket Split Recommended**")
            
            st.caption(f"💡 {routing.reasoning}")
            
            if routing.special_instructions:
                with st.expander("📋 Special Instructions for Agent"):
                    st.markdown(routing.special_instructions)
            
            if routing.requires_split and routing.split_categories:
                with st.expander("✂️ Recommended Ticket Split"):
                    for i, cat in enumerate(routing.split_categories, 1):
                        st.markdown(f"**Ticket {i}**: {cat.value}")


if clear_btn:
    logger.info("Clear button clicked")
    # Clear the text input by removing it from session state
    if 'query_text_input' in st.session_state:
        del st.session_state['query_text_input']
    if 'current_query' in st.session_state:
        del st.session_state['current_query']
    st.rerun()

if reset_btn:
    logger.info("Reset button clicked")
    st.session_state.classifications = []
    if 'query_text_input' in st.session_state:
        del st.session_state['query_text_input']
    if 'current_query' in st.session_state:
        del st.session_state['current_query']
    st.rerun()

# Session Metrics Dashboard
if st.session_state.classifications:
    st.markdown("---")
    st.subheader("📈 Session Analytics")
    
    metrics = calculate_session_metrics()
    df = pd.DataFrame(st.session_state.classifications)
    
    # Summary metrics
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    
    with col_m1:
        st.metric("Total Queries", metrics.total_queries)
    
    with col_m2:
        st.metric("Avg Confidence", f"{metrics.average_confidence:.0%}")
    
    with col_m3:
        st.metric("Rule-Based", f"{metrics.rule_based_percentage():.0f}%")
    
    with col_m4:
        st.metric("Avg Time", f"{metrics.average_response_time_ms:.0f}ms")
    
    with col_m5:
        st.metric("Total Cost", f"${metrics.estimated_total_cost:.4f}")
    
    # Charts
    tab1, tab2, tab3 = st.tabs(["📊 Category Distribution", "⏱️ Performance", "📋 Query History"])
    
    with tab1:
        if metrics.category_distribution:
            # Category distribution pie chart
            fig_cat = go.Figure(data=[go.Pie(
                labels=list(metrics.category_distribution.keys()),
                values=list(metrics.category_distribution.values()),
                hole=0.3
            )])
            fig_cat.update_layout(title="Queries by Category")
            st.plotly_chart(fig_cat, width="stretch")
            
            # Method distribution
            method_counts = df['method'].value_counts()
            fig_method = go.Figure(data=[go.Bar(
                x=method_counts.index,
                y=method_counts.values,
                marker_color=['#1f77b4', '#ff7f0e']
            )])
            fig_method.update_layout(title="Classification Methods Used")
            st.plotly_chart(fig_method, width="stretch")
    
    with tab2:
        # Response time over queries
        fig_time = px.line(
            df,
            y='response_time_ms',
            title='Response Time Over Queries',
            labels={'index': 'Query Number', 'response_time_ms': 'Response Time (ms)'}
        )
        st.plotly_chart(fig_time, width="stretch")
        
        # Confidence distribution
        fig_conf = px.histogram(
            df,
            x='confidence',
            nbins=20,
            title='Confidence Score Distribution',
            labels={'confidence': 'Confidence Score'}
        )
        st.plotly_chart(fig_conf, width="stretch")
    
    with tab3:
        # Query history table
        display_df = df[[
            'query_text',
            'category',
            'confidence',
            'method',
            'response_time_ms'
        ]].copy()
        
        display_df['confidence'] = display_df['confidence'].apply(lambda x: f"{x:.0%}")
        display_df['response_time_ms'] = display_df['response_time_ms'].apply(lambda x: f"{x:.0f}ms")
        display_df = display_df.rename(columns={
            'query_text': 'Query',
            'category': 'Category',
            'confidence': 'Confidence',
            'method': 'Method',
            'response_time_ms': 'Time'
        })
        
        st.dataframe(
            display_df,
            width="stretch",
            hide_index=True
        )
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Session Data (CSV)",
            data=csv,
            file_name=f"classification_session_{st.session_state.session_id[:8]}.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: gray;'>"
    f"QnA Support Application v{settings.app_version} | "
    f"Powered by Azure OpenAI ({settings.azure_openai_model_name})"
    f"</div>",
    unsafe_allow_html=True
)