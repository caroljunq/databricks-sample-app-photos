import os
import io
import streamlit as st
from databricks.sdk import WorkspaceClient

st.set_page_config(page_title="Demo Energia Album", layout="wide")
st.title("Demo Energia Album")

VOLUME_PATH = "/Volumes/workspace_carolina_ferreira_catalog/demo_energia/fotos"
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif")

w = WorkspaceClient()

tab1, tab2 = st.tabs(["📷 Photo Album", "📊 Cliente Table"])

# ---------------------------------------------------------------------------
# TAB 1 — Photo Album
# ---------------------------------------------------------------------------
with tab1:
    st.header("Photo Album")

    uploaded_files = st.file_uploader(
        "Upload images",
        type=["jpg", "jpeg", "png", "gif"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            dest = f"{VOLUME_PATH}/{uploaded_file.name}"
            w.files.upload(dest, uploaded_file.getbuffer(), overwrite=True)
        st.success(f"Saved {len(uploaded_files)} file(s) to {VOLUME_PATH}")

    st.subheader("Gallery")
    try:
        entries = list(w.files.list_directory_contents(VOLUME_PATH))
        images = [
            entry
            for entry in entries
            if entry.path and entry.path.lower().endswith(IMAGE_EXTENSIONS)
        ]
        if images:
            cols = st.columns(3)
            for idx, entry in enumerate(images):
                with cols[idx % 3]:
                    resp = w.files.download(f"/{entry.path}")
                    img_bytes = resp.contents.read()
                    st.image(img_bytes, caption=os.path.basename(entry.path), use_column_width=True)
        else:
            st.info("No images in the album yet. Upload some above!")
    except Exception as e:
        if "NOT_FOUND" in str(e) or "RESOURCE_DOES_NOT_EXIST" in str(e):
            st.warning(f"Volume folder not found: {VOLUME_PATH}")
        else:
            st.error(f"Error reading gallery: {e}")

# ---------------------------------------------------------------------------
# TAB 2 — Cliente Table (lazy load to avoid blocking on cold warehouse)
# ---------------------------------------------------------------------------
with tab2:
    st.header("Cliente Table")

    warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    if not warehouse_id:
        st.error("DATABRICKS_WAREHOUSE_ID não está configurado no app.yaml.")
    else:
        if st.button("Carregar dados", key="load_cliente"):
            import pandas as pd
            from databricks.sdk.service.sql import StatementState

            try:
                with st.spinner("Consultando warehouse..."):
                    response = w.statement_execution.execute_statement(
                        warehouse_id=warehouse_id,
                        statement="SELECT * FROM workspace_carolina_ferreira_catalog.demo_energia.clientes LIMIT 10",
                        wait_timeout="50s",
                    )
                    if response.status and response.status.state == StatementState.SUCCEEDED:
                        columns = [col.name for col in response.manifest.schema.columns]
                        rows = response.result.data_array
                        df = pd.DataFrame(rows, columns=columns)
                        st.dataframe(df, use_container_width=True)
                    else:
                        error_msg = response.status.error.message if response.status.error else "Unknown error"
                        st.error(f"Erro na consulta: {error_msg}")
            except Exception as e:
                st.error(f"Erro ao consultar: {e}")
        else:
            st.info("Clique em **Carregar dados** para executar a consulta.")
