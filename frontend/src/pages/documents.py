import streamlit as st
from src.utils.api import get_chunk_image_path, get_chunk_text_content, make_api_request


def _display_document_summary(doc, chunks):
    """Display document summary with completion stats."""
    total_chunks = len(chunks)
    completed_chunks = sum(1 for chunk in chunks if chunk["completed"])
    completion_percentage = (
        (completed_chunks / total_chunks) * 100 if total_chunks > 0 else 0
    )

    # Show completion summary
    col_summary1, col_summary2 = st.columns([2, 2])
    with col_summary1:
        st.write(f"**Total Chunks:** {total_chunks}")
        st.write(
            f"**Completed:** {completed_chunks}/{total_chunks} ({completion_percentage:.1f}%)"
        )

    with col_summary2:
        # Progress bar
        st.progress(completion_percentage / 100)

    # Show chunk types summary
    text_chunks = sum(1 for chunk in chunks if chunk["type"] == "text")
    image_chunks = sum(1 for chunk in chunks if chunk["type"] == "image")

    chunk_types_info = []
    if text_chunks > 0:
        chunk_types_info.append(f"📝 {text_chunks} text")
    if image_chunks > 0:
        chunk_types_info.append(f"🖼️ {image_chunks} image")

    if chunk_types_info:
        st.write(f"**Chunk Types:** {', '.join(chunk_types_info)}")


def _display_document_header(doc):
    """Display document header with controls."""
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.markdown(f"### 📖 {doc['name']}")
        st.write(f"**Document ID:** {doc['id']}")

    with col2:
        if st.button("👁️ View Chunks", key=f"view_{doc['id']}"):
            st.session_state["viewing_document"] = doc["id"]
            st.rerun()

    with col3:
        if st.button("🗑️ Delete", key=f"delete_{doc['id']}"):
            delete_response = make_api_request("DELETE", f"/document/{doc['id']}")
            if delete_response.status_code == 204:
                st.success(f"Document '{doc['name']}' deleted successfully!")
                st.rerun()
            else:
                st.error("Failed to delete document")


def _display_chunk_content_detailed(chunk, doc_id):
    """Display detailed chunk content."""
    completion_marker = "✅" if chunk["completed"] else "❌"
    st.markdown(
        f"**{completion_marker} Chunk {chunk['id']} - {chunk['type'].title()}**"
    )

    # Show chunk content immediately with completion styling
    if chunk["type"] == "image":
        image_path = get_chunk_image_path(doc_id, chunk["id"])
        if image_path:
            # Add border color based on completion status
            if chunk["completed"]:
                st.success("✅ Completed Image Chunk")
            st.image(image_path, caption=f"Chunk {chunk['id']}", use_column_width=True)
        else:
            st.warning("Image not found")
    else:
        content = get_chunk_text_content(doc_id, chunk["id"])
        if content:
            # Add completion indicator for text chunks
            if chunk["completed"]:
                st.success("✅ Completed Text Chunk")
            st.text_area(
                f"Content for Chunk {chunk['id']}:",
                content,
                height=200,
                key=f"content_{chunk['id']}",
                disabled=True,
            )
        else:
            st.warning("Content not found")


def _display_document_details():
    """Display detailed view for selected document."""
    doc_id = st.session_state["viewing_document"]
    st.divider()
    st.subheader(f"📋 Document Details - ID: {doc_id}")

    # Back button
    if st.button("⬅️ Back to Documents List"):
        del st.session_state["viewing_document"]
        st.rerun()

    # Get document with chunks
    response = make_api_request("GET", f"/document/{doc_id}/full")
    if response.status_code == 200:
        doc_data = response.json()
        document = doc_data["document"]
        chunks = doc_data["chunks"]

        st.write(f"**Document Name:** {document['name']}")
        st.write(f"**Total Chunks:** {len(chunks)}")

        if chunks:
            st.subheader("📑 Chunks")
            for i, chunk in enumerate(chunks):
                # Create a container for each chunk with visible content
                chunk_container = st.container()
                with chunk_container:
                    # Header with chunk info and completion marker
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        # Add completion marker to chunk title
                        completion_marker = "✅" if chunk["completed"] else "❌"
                        st.markdown(
                            f"**{completion_marker} Chunk {chunk['id']} - {chunk['type'].title()}**"
                        )

                    with col2:
                        st.write(f"**Type:** {chunk['type']}")
                        # Show completion status as read-only text
                        status_text = (
                            "✅ Completed" if chunk["completed"] else "❌ Not Completed"
                        )
                        st.write(f"**Status:** {status_text}")

                    # Display chunk content
                    _display_chunk_content_detailed(chunk, doc_id)

                    # Add separator between chunks
                    if i < len(chunks) - 1:
                        st.divider()
        else:
            st.info("No chunks found for this document.")
    else:
        st.error("Failed to load document details")


def show_documents_page():
    """Documents management page"""
    st.title("📄 Document Management")

    # Get all documents
    response = make_api_request("GET", "/document")
    if response.status_code == 200:
        documents = response.json()

        if not documents:
            st.info(
                "No documents found. Go to the Processing page to upload some files!"
            )
        else:
            # Document list
            st.subheader("All Documents")

            for doc in documents:
                # Create a container for each document with visible details
                doc_container = st.container()
                with doc_container:
                    # Document header
                    _display_document_header(doc)

                    # Get and show document chunks summary immediately
                    chunks_response = make_api_request(
                        "GET", f"/document/{doc['id']}/full"
                    )
                    if chunks_response.status_code == 200:
                        chunks_data = chunks_response.json()
                        chunks = chunks_data["chunks"]

                        if chunks:
                            _display_document_summary(doc, chunks)
                        else:
                            st.info("No chunks found")
                    else:
                        st.write("**Status:** Could not load chunk information")

                    # Add separator between documents
                    st.divider()

            # Show detailed view if a document is selected
            if "viewing_document" in st.session_state:
                _display_document_details()
    else:
        st.error("Failed to load documents")
