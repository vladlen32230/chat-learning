import streamlit as st
import requests
import os
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8015"  # Backend API port

# Helper functions
def make_api_request(method: str, endpoint: str, **kwargs) -> requests.Response:
    """Make API request to the backend"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, **kwargs)
        return response
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to the backend API. Make sure the FastAPI server is running on port 8015.")
        st.stop()

def get_static_file_path(document_id: int, chunk_id: int, chunk_type: str) -> Path:
    """Get local static file path"""
    # Get the path to the static folder relative to the frontend directory
    static_dir = Path("../static")
    
    if chunk_type == "image":
        return static_dir / str(document_id) / f"{chunk_id}.jpg"
    else:
        return static_dir / str(document_id) / f"{chunk_id}.txt"

def get_chunk_text_content(document_id: int, chunk_id: int) -> str:
    """Get text chunk content from local static folder"""
    file_path = get_static_file_path(document_id, chunk_id, "text")
    try:
        if file_path.exists():
            return file_path.read_text(encoding='utf-8')
        else:
            return ""
    except Exception:
        return ""

def get_chunk_image_path(document_id: int, chunk_id: int) -> str:
    """Get image chunk path from local static folder"""
    file_path = get_static_file_path(document_id, chunk_id, "image")
    if file_path.exists():
        return str(file_path)
    else:
        return ""

# Page configuration
st.set_page_config(
    page_title="Document Processing & Chat Learning",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("📚 Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    ["📄 Documents", "⚙️ Processing", "👥 Characters"]
)

# Main app logic
if page == "📄 Documents":
    st.title("📄 Document Management")
    
    # Get all documents
    response = make_api_request("GET", "/document")
    if response.status_code == 200:
        documents = response.json()
        
        if not documents:
            st.info("No documents found. Go to the Processing page to upload some files!")
        else:
            # Document list
            st.subheader("All Documents")
            
            for doc in documents:
                # Create a container for each document with visible details
                doc_container = st.container()
                with doc_container:
                    # Document header
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"### 📖 {doc['name']}")
                        st.write(f"**Document ID:** {doc['id']}")
                    
                    with col2:
                        if st.button(f"👁️ View Chunks", key=f"view_{doc['id']}"):
                            st.session_state['viewing_document'] = doc['id']
                            st.rerun()
                    
                    with col3:
                        if st.button(f"🗑️ Delete", key=f"delete_{doc['id']}"):
                            delete_response = make_api_request("DELETE", f"/document/{doc['id']}")
                            if delete_response.status_code == 204:
                                st.success(f"Document '{doc['name']}' deleted successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to delete document")
                    
                    # Get and show document chunks summary immediately
                    chunks_response = make_api_request("GET", f"/document/{doc['id']}/full")
                    if chunks_response.status_code == 200:
                        chunks_data = chunks_response.json()
                        chunks = chunks_data['chunks']
                        
                        if chunks:
                            total_chunks = len(chunks)
                            completed_chunks = sum(1 for chunk in chunks if chunk['completed'])
                            completion_percentage = (completed_chunks / total_chunks) * 100 if total_chunks > 0 else 0
                            
                            # Show completion summary
                            col_summary1, col_summary2 = st.columns([2, 2])
                            with col_summary1:
                                st.write(f"**Total Chunks:** {total_chunks}")
                                st.write(f"**Completed:** {completed_chunks}/{total_chunks} ({completion_percentage:.1f}%)")
                            
                            with col_summary2:
                                # Progress bar
                                st.progress(completion_percentage / 100)
                            
                            # Show chunk types summary
                            text_chunks = sum(1 for chunk in chunks if chunk['type'] == 'text')
                            image_chunks = sum(1 for chunk in chunks if chunk['type'] == 'image')
                            
                            chunk_types_info = []
                            if text_chunks > 0:
                                chunk_types_info.append(f"📝 {text_chunks} text")
                            if image_chunks > 0:
                                chunk_types_info.append(f"🖼️ {image_chunks} image")
                            
                            if chunk_types_info:
                                st.write(f"**Chunk Types:** {', '.join(chunk_types_info)}")
                        else:
                            st.write("**Status:** No chunks found")
                    else:
                        st.write("**Status:** Could not load chunk information")
                    
                    # Add separator between documents
                    st.divider()

            # Show detailed view if a document is selected
            if 'viewing_document' in st.session_state:
                doc_id = st.session_state['viewing_document']
                st.divider()
                st.subheader(f"📋 Document Details - ID: {doc_id}")
                
                # Back button
                if st.button("⬅️ Back to Documents List"):
                    del st.session_state['viewing_document']
                    st.rerun()
                
                # Get document with chunks
                response = make_api_request("GET", f"/document/{doc_id}/full")
                if response.status_code == 200:
                    doc_data = response.json()
                    document = doc_data['document']
                    chunks = doc_data['chunks']
                    
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
                                    completion_marker = "✅" if chunk['completed'] else "❌"
                                    st.markdown(f"**{completion_marker} Chunk {chunk['id']} - {chunk['type'].title()}**")
                                
                                with col2:
                                    st.write(f"**Type:** {chunk['type']}")
                                    # Show completion status as read-only text
                                    status_text = "✅ Completed" if chunk['completed'] else "❌ Not Completed"
                                    st.write(f"**Status:** {status_text}")
                                
                                # Show chunk content immediately with completion styling
                                if chunk['type'] == 'image':
                                    image_path = get_chunk_image_path(doc_id, chunk['id'])
                                    if image_path:
                                        # Add border color based on completion status
                                        if chunk['completed']:
                                            st.success("✅ Completed Image Chunk")
                                        st.image(image_path, caption=f"Chunk {chunk['id']}", use_column_width=True)
                                    else:
                                        st.warning("Image not found")
                                else:
                                    content = get_chunk_text_content(doc_id, chunk['id'])
                                    if content:
                                        # Add completion indicator for text chunks
                                        if chunk['completed']:
                                            st.success("✅ Completed Text Chunk")
                                        st.text_area(
                                            f"Content for Chunk {chunk['id']}:", 
                                            content, 
                                            height=200, 
                                            key=f"content_{chunk['id']}",
                                            disabled=True
                                        )
                                    else:
                                        st.warning("Content not found")
                                
                                # Add separator between chunks
                                if i < len(chunks) - 1:
                                    st.divider()
                    else:
                        st.info("No chunks found for this document.")
                else:
                    st.error("Failed to load document details")
    else:
        st.error("Failed to load documents")

elif page == "⚙️ Processing":
    st.title("⚙️ File Processing")
    
    st.write("Upload PDF files or images to create new documents with chunked content.")
    
    # Initialize session state for files if not exists
    if 'uploaded_files_list' not in st.session_state:
        st.session_state.uploaded_files_list = []
    if 'document_name' not in st.session_state:
        st.session_state.document_name = ""
    
    # Document name input
    st.subheader("📝 Document Information")
    document_name = st.text_input(
        "Document Name:", 
        value=st.session_state.document_name,
        placeholder="Enter a name for your document",
        key="doc_name_input"
    )
    st.session_state.document_name = document_name
    
    st.subheader("📤 Upload Files")
    st.write("Add files one by one in the order you want them processed (top to bottom).")
    
    # Display current files list
    if st.session_state.uploaded_files_list:
        st.write("**Current Files (in processing order):**")
        
        for i, file_info in enumerate(st.session_state.uploaded_files_list):
            col1, col2, col3 = st.columns([1, 4, 1])
            
            with col1:
                st.write(f"**{i+1}.**")
            
            with col2:
                file_type_icon = "📄" if file_info['type'] == "application/pdf" or file_info['name'].lower().endswith('.pdf') else "🖼️"
                st.write(f"{file_type_icon} {file_info['name']}")
                st.caption(f"Size: {file_info['size']} bytes")
            
            with col3:
                if st.button("🗑️", key=f"remove_{i}", help="Remove this file"):
                    st.session_state.uploaded_files_list.pop(i)
                    st.rerun()
        
        st.divider()
    
    # File upload row
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a file:",
            type=["pdf", "jpg", "jpeg", "png"],
            accept_multiple_files=False,
            help="Upload PDF files or images (JPG, JPEG, PNG)",
            key=f"file_uploader_{len(st.session_state.uploaded_files_list)}"
        )
    
    with col2:
        if st.button("📤 Add File", disabled=uploaded_file is None):
            if uploaded_file is not None:
                # Store file info and content
                file_info = {
                    'name': uploaded_file.name,
                    'type': uploaded_file.type,
                    'size': uploaded_file.size,
                    'content': uploaded_file.getvalue()
                }
                st.session_state.uploaded_files_list.append(file_info)
                st.rerun()
    
    # Process all files button
    if st.session_state.uploaded_files_list and document_name:
        st.divider()
        
        # Show summary
        pdf_count = sum(1 for f in st.session_state.uploaded_files_list if f['type'] == "application/pdf" or f['name'].lower().endswith('.pdf'))
        image_count = len(st.session_state.uploaded_files_list) - pdf_count
        
        file_info = []
        if pdf_count > 0:
            file_info.append(f"📄 {pdf_count} PDF file(s)")
        if image_count > 0:
            file_info.append(f"🖼️ {image_count} image file(s)")
        
        if file_info:
            st.info(f"Ready to process: {', '.join(file_info)} in the order shown above")
        
        if st.button("🚀 Process All Files", type="primary"):
            # Prepare files for API in the correct order
            files_data = []
            for file_info in st.session_state.uploaded_files_list:
                files_data.append(
                    ("files", (file_info['name'], file_info['content'], file_info['type']))
                )
            
            # Prepare form data
            form_data = {
                "name": document_name
            }
            
            with st.spinner("Processing files... This may take a while."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/document",
                        files=files_data,
                        data=form_data
                    )
                    
                    if response.status_code == 201:
                        document = response.json()
                        st.success(f"✅ Document '{document['name']}' created successfully!")
                        st.success(f"Document ID: {document['id']}")
                        
                        # Clear the uploaded files list and document name
                        st.session_state.uploaded_files_list = []
                        st.session_state.document_name = ""
                        
                        # Auto-redirect to document view
                        st.info("Redirecting to document view...")
                        st.session_state['viewing_document'] = document['id']
                        
                        # Switch to documents page
                        if st.button("📄 View Document"):
                            st.switch_page("📄 Documents")
                    else:
                        st.error(f"Failed to process files: {response.text}")
                except Exception as e:
                    st.error(f"Error processing files: {str(e)}")
    
    elif st.session_state.uploaded_files_list and not document_name:
        st.warning("Please enter a document name to process the files.")
    elif not st.session_state.uploaded_files_list and document_name:
        st.info("Add some files to process.")
    
    # Clear all button
    if st.session_state.uploaded_files_list:
        st.divider()
        if st.button("🗑️ Clear All Files", type="secondary"):
            st.session_state.uploaded_files_list = []
            st.session_state.document_name = ""
            st.rerun()

elif page == "👥 Characters":
    st.title("👥 Character Management")
    
    # Get all characters
    response = make_api_request("GET", "/character")
    
    if response.status_code == 200:
        characters = response.json()
        
        # Create new character form
        with st.expander("➕ Create New Character", expanded=False):
            with st.form("character_form"):
                st.subheader("New Character")
                
                name = st.text_input("Character Name:", placeholder="Enter character name")
                prompt_description = st.text_area(
                    "Prompt Description:", 
                    placeholder="Enter character description/prompt",
                    height=100
                )
                
                voice_options = ['af_bella', 'af_nicole', 'af_heart', 'af_nova']
                voice_name = st.selectbox(
                    "Voice Name (Optional):", 
                    [None] + voice_options,
                    format_func=lambda x: "None" if x is None else x
                )
                
                submit_character = st.form_submit_button("👤 Create Character")
                
                if submit_character:
                    if not name or not prompt_description:
                        st.error("Please fill in all required fields")
                    else:
                        character_data = {
                            "name": name,
                            "prompt_description": prompt_description,
                            "voice_name": voice_name
                        }
                        
                        create_response = make_api_request("POST", "/character", json=character_data)
                        if create_response.status_code == 201:
                            st.success(f"Character '{name}' created successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to create character")
        
        # Display existing characters
        st.subheader("Existing Characters")
        
        if not characters:
            st.info("No characters found. Create your first character above!")
        else:
            for character in characters:
                with st.expander(f"👤 {character['name']} (ID: {character['id']})"):
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.write(f"**Name:** {character['name']}")
                        st.write(f"**Voice:** {character['voice_name'] or 'None'}")
                        st.write(f"**Description:**")
                        st.write(character['prompt_description'])
                    
                    with col2:
                        if st.button(f"🗑️ Delete", key=f"delete_char_{character['id']}"):
                            delete_response = make_api_request("DELETE", f"/character/{character['id']}")
                            if delete_response.status_code == 204:
                                st.success(f"Character '{character['name']}' deleted successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to delete character")
    else:
        st.error("Failed to load characters")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **📚 Document Processing & Chat Learning**
    
    This app interfaces with your FastAPI backend to:
    - 📄 Manage documents and chunks
    - ⚙️ Process files (PDF/Images)
    - 👥 Create and manage characters
    
    **Servers:**
    - Backend API: `localhost:8015`
    - Static Files: Local filesystem access
    """
) 