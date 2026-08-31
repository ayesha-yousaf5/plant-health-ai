"""
Sidebar chatbot component - integrated into Streamlit's sidebar.
"""

import streamlit as st
from chatbot.plantcare_ai import ask


def render_sidebar_chatbot():
    """Render a chatbot in the Streamlit sidebar."""
    
    # Initialize chatbot state if not exists
    if "sidebar_chat_history" not in st.session_state:
        st.session_state.sidebar_chat_history = []
    
    # Get diagnosis context if available
    result = st.session_state.get("diagnosis_result")
    context = result if result and not result.get("uncertain") else {}
    
    # Add chatbot to sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 💬 PlantCare AI Assistant")
        
        # Show context if diagnosis exists
        if context and context.get("disease"):
            st.info(f"Context: {context.get('crop', 'Unknown')} - {context.get('disease')}")
        
        # Display chat history
        if st.session_state.sidebar_chat_history:
            chat_container = st.container(height=400)
            with chat_container:
                for turn in st.session_state.sidebar_chat_history:
                    if turn["role"] == "user":
                        st.markdown(f"**You:** {turn['content']}")
                    else:
                        st.markdown(f"**🌿 Assistant:** {turn['content']}")
        else:
            st.caption("Ask me about your plant diseases! Try: 'What should I do?' or 'How to treat?'")
        
        # Chat input
        with st.form(key="sidebar_chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Ask a question:",
                key="sidebar_chat_input",
                placeholder="e.g., What should I do?",
                label_visibility="collapsed"
            )
            submit_button = st.form_submit_button("Send", use_container_width=True)
            
            if submit_button and user_input:
                # Add user message
                st.session_state.sidebar_chat_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                # Get AI response
                with st.spinner("Thinking..."):
                    try:
                        reply = ask(user_input, context, st.session_state.sidebar_chat_history)
                    except Exception as e:
                        reply = f"Sorry, I encountered an error: {str(e)}"
                
                # Add AI response
                st.session_state.sidebar_chat_history.append({
                    "role": "assistant",
                    "content": reply
                })
                
                st.rerun()
        
        # Clear chat and full page link
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Chat", key="clear_sidebar_chat", use_container_width=True):
                st.session_state.sidebar_chat_history = []
                st.rerun()
        with col2:
            st.page_link("pages/3_🤖_Assistant.py", label="Full Page →", icon="💬")
