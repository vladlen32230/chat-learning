import base64

import requests
import streamlit as st
from src.utils.api import (
    API_BASE_URL,
    get_chunk_image_path,
    get_chunk_text_content,
    make_api_request,
)


def _initialize_session_state():
    """Initialize session state for chat."""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = {}  # {(doc_id, chunk_id): [messages]}
    if "selected_document_id" not in st.session_state:
        st.session_state.selected_document_id = None
    if "selected_character_id" not in st.session_state:
        st.session_state.selected_character_id = None


def _select_document():
    """Handle document selection."""
    st.subheader("📖 Select Document")
    doc_response = make_api_request("GET", "/document")
    if doc_response.status_code == 200:
        documents = doc_response.json()
        if documents:
            doc_options = {doc["id"]: doc["name"] for doc in documents}
            selected_doc_id = st.selectbox(
                "Choose a document:",
                options=list(doc_options.keys()),
                format_func=lambda x: f"{doc_options[x]} (ID: {x})",
                key="doc_selector",
            )
            st.session_state.selected_document_id = selected_doc_id
        else:
            st.info("No documents available. Please create some documents first.")
            st.session_state.selected_document_id = None
    else:
        st.error("Failed to load documents")
        st.session_state.selected_document_id = None


def _select_character():
    """Handle character selection."""
    st.subheader("👤 Select Character")
    char_response = make_api_request("GET", "/character")
    if char_response.status_code == 200:
        characters = char_response.json()
        if characters:
            char_options = {char["id"]: char["name"] for char in characters}
            selected_char_id = st.selectbox(
                "Choose a character:",
                options=list(char_options.keys()),
                format_func=lambda x: f"{char_options[x]} (ID: {x})",
                key="char_selector",
            )
            st.session_state.selected_character_id = selected_char_id
        else:
            st.info("No characters available. Please create some characters first.")
            st.session_state.selected_character_id = None
    else:
        st.error("Failed to load characters")
        st.session_state.selected_character_id = None


def _handle_completion_toggle(chunk):
    """Handle chunk completion status toggle."""
    current_completed = chunk["completed"]
    button_text = "✅ Completed" if current_completed else "❌ Mark Complete"
    button_type = "secondary" if current_completed else "primary"

    if st.button(
        button_text,
        key=f"toggle_completed_{chunk['id']}",
        type=button_type,
        help="Click to toggle completion status",
    ):
        new_completed = not current_completed
        try:
            update_response = make_api_request(
                "PUT",
                f"/document/{st.session_state.selected_document_id}/chunk/{chunk['id']}",
                json={"completed": new_completed},
            )
            if update_response.status_code == 200:
                st.rerun()
            else:
                st.error(f"Failed to update chunk: {update_response.text}")
        except Exception as e:
            st.error(f"Error updating chunk: {str(e)}")


def _handle_chat_toggle(chunk):
    """Handle chat window toggle."""
    chat_key = f"{st.session_state.selected_document_id}_{chunk['id']}"
    is_chat_open = st.session_state.get(f"chat_open_{chat_key}", False)

    if st.button(
        f"💬 {'Close Chat' if is_chat_open else 'Chat'}",
        key=f"chat_{chunk['id']}",
        type="primary" if chunk["completed"] else "secondary",
    ):
        st.session_state[f"chat_open_{chat_key}"] = not is_chat_open
        if not is_chat_open:
            if chat_key not in st.session_state.chat_messages:
                st.session_state.chat_messages[chat_key] = []
        st.rerun()


def _display_chunk_content(chunk):
    """Display chunk content."""
    completion_marker = "✅" if chunk["completed"] else "❌"
    st.markdown(
        f"**{completion_marker} Chunk {chunk['id']} - {chunk['type'].title()}**"
    )

    if chunk["type"] == "image":
        image_path = get_chunk_image_path(
            st.session_state.selected_document_id, chunk["id"]
        )
        if image_path:
            st.image(image_path, caption=f"Chunk {chunk['id']}", use_column_width=True)
        else:
            st.warning("Image not found")
    else:
        content = get_chunk_text_content(
            st.session_state.selected_document_id, chunk["id"]
        )
        if content:
            formatted_content = content.replace("\n", "<br>")
            st.markdown(
                f"""
            <div style="background-color: #1e1e1e; padding: 15px; border-radius: 5px; color: white; font-family: monospace;">
            {formatted_content}
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.warning("Content not found")


def _display_chat_messages(messages):
    """Display chat message history."""
    if messages:
        st.subheader("💭 Chat History")
        for msg in messages:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(msg["content"])
                    if "audio" in msg and msg["audio"]:
                        try:
                            if msg["audio"].startswith("data:audio/mp3;base64,"):
                                base64_data = msg["audio"].split(",", 1)[1]
                            else:
                                base64_data = msg["audio"]
                            audio_data = base64.b64decode(base64_data)
                            st.audio(audio_data, format="audio/mp3")
                        except Exception as e:
                            st.warning(f"Could not play audio: {str(e)}")


def _send_chat_message(chunk, chat_key, user_message, wav_audio_data, selected_model):
    """Handle sending a chat message."""
    if not st.session_state.selected_character_id:
        st.error("Please select a character first")
        return

    with st.spinner("Sending message..."):
        try:
            if wav_audio_data:
                # Handle audio message
                import json

                form_data = {
                    "character_id": str(st.session_state.selected_character_id),
                    "messages_history": json.dumps(
                        [
                            {"role": msg["role"], "content": msg["content"]}
                            for msg in st.session_state.chat_messages[chat_key]
                        ]
                    ),
                    "model": selected_model,
                }

                if user_message.strip():
                    form_data["new_message_text"] = user_message.strip()

                files = {
                    "new_message_speech": ("audio.wav", wav_audio_data, "audio/wav")
                }
                response = requests.post(
                    f"{API_BASE_URL}/chat/document/{st.session_state.selected_document_id}/chunk/{chunk['id']}",
                    data=form_data,
                    files=files,
                )
            else:
                # Handle text-only message
                chat_data = {
                    "character_id": st.session_state.selected_character_id,
                    "messages_history": [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in st.session_state.chat_messages[chat_key]
                    ],
                    "new_message_text": user_message.strip(),
                    "model": selected_model,
                }
                response = requests.post(
                    f"{API_BASE_URL}/chat/document/{st.session_state.selected_document_id}/chunk/{chunk['id']}",
                    json=chat_data,
                )

            if response.status_code == 200:
                chat_response = response.json()

                # Add user message to history
                user_msg_content = (
                    chat_response.get("input_user_text")
                    or user_message.strip()
                    or "[Voice message]"
                )
                st.session_state.chat_messages[chat_key].append(
                    {
                        "role": "user",
                        "content": user_msg_content,
                    }
                )

                # Add assistant response to history
                assistant_msg = {
                    "role": "assistant",
                    "content": chat_response["text"],
                }
                if chat_response.get("speech"):
                    assistant_msg["audio"] = chat_response["speech"]

                st.session_state.chat_messages[chat_key].append(assistant_msg)
                st.success("Message sent successfully!")
                st.rerun()
            else:
                st.error(f"Failed to send message: {response.text}")
        except Exception as e:
            st.error(f"Error sending message: {str(e)}")


def _display_chat_interface(chunk, chat_key):
    """Display the chat interface for a chunk."""
    st.markdown("---")
    st.markdown("**🎯 Discussing this content:**")

    messages = st.session_state.chat_messages[chat_key]
    _display_chat_messages(messages)

    # Chat input section
    st.subheader("✍️ Send Message")

    # Model selection
    model_col, input_col = st.columns([1, 3])
    with model_col:
        selected_model = st.selectbox(
            "Model:",
            options=[
                "google/gemini-2.5-flash-preview-05-20",
                "google/gemini-2.5-pro-preview",
            ],
            key=f"model_selector_{chunk['id']}",
        )

    with input_col:
        user_message = st.text_area(
            "Your message:",
            placeholder="Type your message here...",
            height=100,
            key=f"chat_input_{chunk['id']}",
        )

    # Microphone input section
    st.markdown("---")
    st.markdown("🎤 **Voice Input** (Record with microphone)")

    audio_container = st.container()
    with audio_container:
        try:
            from st_audiorec import st_audiorec

            wav_audio_data = st_audiorec()
            if wav_audio_data is not None:
                st.success("🎵 Audio recorded successfully!")
        except Exception as e:
            st.error(f"❌ Audio recording error: {str(e)}")
            wav_audio_data = None

    # Send button
    send_col1, send_col2 = st.columns([1, 4])
    with send_col1:
        send_button = st.button(
            "📤 Send",
            type="primary",
            key=f"send_message_{chunk['id']}",
        )

    if send_button and (user_message.strip() or wav_audio_data):
        _send_chat_message(
            chunk, chat_key, user_message, wav_audio_data, selected_model
        )


def show_chat_page():
    """Chat learning page"""
    st.title("💬 Chat Learning")

    # Initialize session state for chat
    _initialize_session_state()

    # Top selection row
    col1, col2 = st.columns(2)

    with col1:
        _select_document()

    with col2:
        _select_character()

    # Show chunks if both document and character are selected
    if st.session_state.selected_document_id and st.session_state.selected_character_id:
        st.divider()

        # Get document with chunks
        doc_full_response = make_api_request(
            "GET", f"/document/{st.session_state.selected_document_id}/full"
        )
        if doc_full_response.status_code == 200:
            doc_data = doc_full_response.json()
            document = doc_data["document"]
            chunks = doc_data["chunks"]

            st.subheader(f"📑 Chunks from '{document['name']}'")

            if chunks:
                # Display chunks in a single column
                for chunk in chunks:
                    chunk_container = st.container()
                    with chunk_container:
                        # Completion toggle and chat button row
                        toggle_col, chat_col = st.columns([1, 1])

                        with toggle_col:
                            _handle_completion_toggle(chunk)

                        with chat_col:
                            _handle_chat_toggle(chunk)

                        # Chunk info and content
                        _display_chunk_content(chunk)

                        # Show chat window directly under this chunk if open
                        chat_key = (
                            f"{st.session_state.selected_document_id}_{chunk['id']}"
                        )
                        if st.session_state.get(f"chat_open_{chat_key}", False):
                            _display_chat_interface(chunk, chat_key)

                        st.divider()
            else:
                st.info("No chunks found for this document.")
        else:
            st.error("Failed to load document chunks")
