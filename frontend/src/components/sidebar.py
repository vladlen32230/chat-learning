import streamlit as st


def show_sidebar():
    """Show sidebar navigation and footer"""
    st.sidebar.title("📚 Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:", ["📄 Documents", "⚙️ Processing", "👥 Characters", "💬 Chat"]
    )

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        **📚 Document Processing & Chat Learning**

        This app interfaces with your FastAPI backend to:
        - 📄 Manage documents and chunks
        - ⚙️ Process files (PDF/Images)
        - 👥 Create and manage characters
        - 💬 Chat with AI about content

        **Servers:**
        - Backend API: `localhost:8015`
        - Frontend: `localhost:8516`
        """
    )

    return page
