import streamlit as st
from streamlit_app.api_client import AdvisoryAPIClient


def render_memory_viewer(api_client: AdvisoryAPIClient):
    st.subheader("🧠 Long-Term Advisory Memory Viewer")

    client_id = st.text_input("Enter or select Client ID to query long-term memory:", value="C1001")

    if st.button("🔍 Query Memories"):
        if not client_id.strip():
            st.error("Please enter a valid Client ID.")
            return

        with st.spinner(f"Retrieving memories for Client {client_id}..."):
            data = api_client.get_client_memory(client_id.strip())
            memories = data.get("memories", [])
            count = data.get("count", 0)

            st.markdown(f"#### Memory Records for Client: `{client_id}` ({count} entry/entries found)")

            if memories:
                for idx, mem in enumerate(memories, 1):
                    with st.container():
                        st.markdown(f"##### Memory Entry #{idx}")
                        st.info(mem)
            else:
                st.warning(f"No historical memory records found for Client ID '{client_id}'.")
