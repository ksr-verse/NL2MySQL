#!/usr/bin/env python3
"""Streamlit frontend for IIQ Natural Language to SQL Copilot."""

import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="IIQ Natural Language to SQL Copilot",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .query-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .sql-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        font-family: 'Courier New', monospace;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"

def check_api_connection() -> bool:
    """Check if the API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def call_api_endpoint(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Call API endpoint and return response."""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {"error": str(e)}

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<h1 class="main-header">🔍 IIQ Natural Language to SQL Copilot</h1>', unsafe_allow_html=True)
    
    # Check API connection
    if not check_api_connection():
        st.error("❌ API is not running. Please start the API server with: `python app.py`")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("📊 System Status")
        
        # API Status
        if check_api_connection():
            st.success("✅ API Connected")
        else:
            st.error("❌ API Disconnected")
        
        # System Metrics
        st.subheader("📈 System Metrics")
        
        # Placeholder for metrics (would be populated from API)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Queries Today", "0", "0")
        with col2:
            st.metric("Success Rate", "0%", "0%")
        
        # Configuration
        st.subheader("⚙️ Configuration")
        
        # Query parameters
        max_rows = st.slider("Max Rows", 10, 1000, 100)
        include_explanation = st.checkbox("Include Explanation", value=False)
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            use_synonyms = st.checkbox("Use Synonyms", value=True)
            use_learning = st.checkbox("Use Learning Data", value=True)
            validate_sql = st.checkbox("Validate SQL", value=True)
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Query", "📊 Results", "📚 Learning", "⚙️ Admin"])
    
    with tab1:
        st.header("Natural Language Query")
        
        # Query input
        user_query = st.text_area(
            "Enter your natural language query:",
            placeholder="e.g., Give me employees (first name, last name, display name, email, manager) who have accounts in Workday, Trakk, Finance, and Apache DS. They must also have capability TimeSheetEnterAuthority in Trakk and belong to the PayrollAnalysis group in Finance.",
            height=100
        )
        
        # Query buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🚀 Generate SQL", type="primary"):
                if user_query:
                    with st.spinner("Generating SQL..."):
                        # Call API
                        data = {
                            "question": user_query,
                            "max_rows": max_rows,
                            "include_explanation": include_explanation
                        }
                        
                        response = call_api_endpoint("/query", data)
                        
                        if "error" not in response:
                            st.session_state['last_query'] = user_query
                            st.session_state['last_sql'] = response.get('sql', '')
                            st.session_state['last_explanation'] = response.get('explanation', '')
                            st.session_state['last_response'] = response
                        else:
                            st.error(f"Error: {response['error']}")
                else:
                    st.warning("Please enter a query first.")
        
        with col2:
            if st.button("🔄 Clear"):
                st.session_state.clear()
                st.rerun()
        
        # Display generated SQL
        if 'last_sql' in st.session_state:
            st.subheader("Generated SQL")
            
            # SQL display
            st.markdown('<div class="sql-box">', unsafe_allow_html=True)
            st.code(st.session_state['last_sql'], language='sql')
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Explanation
            if st.session_state.get('last_explanation'):
                st.subheader("Explanation")
                st.info(st.session_state['last_explanation'])
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("▶️ Execute Query"):
                    if 'last_sql' in st.session_state:
                        with st.spinner("Executing query..."):
                            data = {
                                "sql": st.session_state['last_sql'],
                                "max_rows": max_rows
                            }
                            
                            response = call_api_endpoint("/execute", data)
                            
                            if "error" not in response:
                                st.session_state['last_results'] = response
                            else:
                                st.error(f"Execution Error: {response['error']}")
            
            with col2:
                if st.button("📝 Provide Feedback"):
                    st.session_state['show_feedback'] = True
            
            with col3:
                if st.button("💾 Save Query"):
                    # Save to learning data
                    st.success("Query saved to learning data!")
    
    with tab2:
        st.header("Query Results")
        
        if 'last_results' in st.session_state:
            results = st.session_state['last_results']
            
            if 'data' in results and results['data']:
                # Display results as table
                df = pd.DataFrame(results['data'])
                st.dataframe(df, use_container_width=True)
                
                # Results summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows Returned", len(results['data']))
                with col2:
                    st.metric("Execution Time", f"{results.get('execution_time', 0):.2f}s")
                with col3:
                    st.metric("Query Status", "Success" if results.get('success', False) else "Failed")
            else:
                st.warning("No data returned from query.")
        else:
            st.info("No query results to display. Generate and execute a query first.")
    
    with tab3:
        st.header("Learning & Feedback")
        
        # Feedback form
        if st.session_state.get('show_feedback', False):
            st.subheader("Provide Feedback")
            
            with st.form("feedback_form"):
                original_query = st.text_input("Original Query", value=st.session_state.get('last_query', ''))
                generated_sql = st.text_area("Generated SQL", value=st.session_state.get('last_sql', ''))
                corrected_sql = st.text_area("Corrected SQL (if any)")
                feedback_notes = st.text_area("Feedback Notes")
                dba_user = st.text_input("DBA User", value="user")
                
                submitted = st.form_submit_button("Submit Feedback")
                
                if submitted:
                    # Submit feedback
                    st.success("Feedback submitted successfully!")
                    st.session_state['show_feedback'] = False
        
        # Learning examples
        st.subheader("Learning Examples")
        
        # Placeholder for learning examples
        st.info("Learning examples will be displayed here once the system has collected feedback data.")
    
    with tab4:
        st.header("Admin Panel")
        
        # System status
        st.subheader("System Status")
        
        # API Health
        if check_api_connection():
            st.success("✅ API is running")
        else:
            st.error("❌ API is not running")
        
        # Configuration
        st.subheader("Configuration")
        
        # Database connection
        st.text_input("Database Connection", value="mysql+pymysql://root:root@localhost:3306/identityiq", disabled=True)
        
        # LLM Configuration
        st.text_input("LLM Provider", value="sqlcoder", disabled=True)
        st.text_input("LLM Model", value="defog/sqlcoder-7b-2", disabled=True)
        
        # Vector Database
        st.text_input("Vector DB", value="ChromaDB", disabled=True)
        st.text_input("Embeddings Model", value="all-MiniLM-L6-v2", disabled=True)
        
        # Actions
        st.subheader("Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refresh Schema"):
                st.info("Schema refresh initiated...")
        
        with col2:
            if st.button("📊 View Logs"):
                st.info("Logs will be displayed here...")

if __name__ == "__main__":
    main()
