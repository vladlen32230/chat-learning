import streamlit as st
import requests
from src.utils.api import make_api_request, API_BASE_URL

def show_processing_page():
    """File processing page"""
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