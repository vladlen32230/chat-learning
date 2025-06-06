import streamlit as st
from src.components.sidebar import show_sidebar
from src.pages.characters import show_characters_page
from src.pages.chat_interface import show_chat_page
from src.pages.documents import show_documents_page
from src.pages.processing import show_processing_page

# Page configuration
st.set_page_config(
    page_title="Document Processing & Chat Learning",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main application entry point"""
    # Show sidebar and get selected page
    page = show_sidebar()

    # Route to appropriate page
    if page == "📄 Documents":
        show_documents_page()
    elif page == "⚙️ Processing":
        show_processing_page()
    elif page == "👥 Characters":
        show_characters_page()
    elif page == "💬 Chat":
        show_chat_page()


if __name__ == "__main__":
    main()
