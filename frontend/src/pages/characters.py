import streamlit as st
from src.utils.api import make_api_request


def show_characters_page():
    """Character management page"""
    st.title("👥 Character Management")

    # Get all characters
    response = make_api_request("GET", "/character")

    if response.status_code == 200:
        characters = response.json()

        # Create new character form
        with st.expander("➕ Create New Character", expanded=False):
            with st.form("character_form"):
                st.subheader("New Character")

                name = st.text_input(
                    "Character Name:", placeholder="Enter character name"
                )
                prompt_description = st.text_area(
                    "Prompt Description:",
                    placeholder="Enter character description/prompt",
                    height=100,
                )

                voice_options = ["af_bella", "af_nicole", "af_heart", "af_nova"]
                voice_name = st.selectbox(
                    "Voice Name (Optional):",
                    [None] + voice_options,
                    format_func=lambda x: "None" if x is None else x,
                )

                submit_character = st.form_submit_button("👤 Create Character")

                if submit_character:
                    if not name or not prompt_description:
                        st.error("Please fill in all required fields")
                    else:
                        character_data = {
                            "name": name,
                            "prompt_description": prompt_description,
                            "voice_name": voice_name,
                        }

                        create_response = make_api_request(
                            "POST", "/character", json=character_data
                        )
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
                        st.write("**Description:**")
                        st.write(character["prompt_description"])

                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_char_{character['id']}"):
                            delete_response = make_api_request(
                                "DELETE", f"/character/{character['id']}"
                            )
                            if delete_response.status_code == 204:
                                st.success(
                                    f"Character '{character['name']}' deleted successfully!"
                                )
                                st.rerun()
                            else:
                                st.error("Failed to delete character")
    else:
        st.error("Failed to load characters")
