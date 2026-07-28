"""Demo Energia Album — Databricks App (Streamlit).

Abas:
  1) Photo Album  — upload/galeria em Unity Catalog Volume
  2) Cliente Table — SELECT via SQL Warehouse
  3) Dados Lakebase — CRUD em Postgres (Lakebase Autoscaling)
  4) AI/BI Dashboard — Embed de dashboard AI/BI

Variáveis de ambiente esperadas (ver app.yaml + runbook):
  DATABRICKS_WAREHOUSE_ID  — ID do SQL Warehouse
  LAKEBASE_ENDPOINT        — valueFrom: postgres (path do endpoint)
  PGHOST / PGDATABASE / PGPORT / PGUSER / PGSSLMODE — injetadas pelo recurso postgres
  DATABRICKS_CLIENT_ID     — injetada pelo runtime (SP do app); fallback de PGUSER
  VOLUME_PATH              — path do volume UC (opcional; default abaixo)
  CLIENTES_TABLE           — tabela UC fully-qualified (opcional; default abaixo)
"""

import os
from io import BytesIO

import psycopg2
import streamlit as st
from databricks.sdk import WorkspaceClient

st.set_page_config(page_title="Demo Energia Album", layout="wide")
st.title("Demo Energia Album")

VOLUME_PATH = os.environ.get("VOLUME_PATH")
CLIENTES_TABLE = os.environ.get("CLIENTES_TABLE")
DASHBOARD_ID = os.environ.get("DASHBOARD_ID")
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif")


@st.cache_resource
def get_workspace_client():
    return WorkspaceClient()


w = get_workspace_client()


def get_lakebase_connection():
    """Conexão psycopg2 com token OAuth do Lakebase Autoscaling.

    Requer recurso `postgres` anexado ao app e LAKEBASE_ENDPOINT via valueFrom.
    Token expira em ~60 min — gerar a cada conexão.
    """
    endpoint_name = os.environ["LAKEBASE_ENDPOINT"]
    pg_host = os.environ["PGHOST"]
    db = os.environ.get("PGDATABASE", "databricks_postgres")
    pg_port = os.environ.get("PGPORT", "5432")
    pg_user = os.environ.get("PGUSER") or os.environ["DATABRICKS_CLIENT_ID"]

    pg_token = get_workspace_client().postgres.generate_database_credential(
        endpoint=endpoint_name
    ).token

    return psycopg2.connect(
        host=pg_host,
        port=pg_port,
        dbname=db,
        user=pg_user,
        password=pg_token,
        sslmode=os.environ.get("PGSSLMODE", "require"),
    )


tab1, tab2, tab3, tab4 = st.tabs(["📷 Photo Album", "📊 Cliente Table", "🗄️ Dados Lakebase", "📈 AI/BI Dashboard"])

# ---------------------------------------------------------------------------
# TAB 1 — Photo Album
# ---------------------------------------------------------------------------
with tab1:
    st.header("Photo Album")
    st.caption(f"Volume: `{VOLUME_PATH}`")

    uploaded_files = st.file_uploader(
        "Upload images",
        type=["jpg", "jpeg", "png", "gif"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            dest = f"{VOLUME_PATH}/{uploaded_file.name}"
            w.files.upload(dest, BytesIO(uploaded_file.getbuffer()), overwrite=True)
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
                    st.image(
                        img_bytes,
                        caption=os.path.basename(entry.path),
                        use_column_width=True,
                    )
        else:
            st.info("No images in the album yet. Upload some above!")
    except Exception as e:
        if "NOT_FOUND" in str(e) or "RESOURCE_DOES_NOT_EXIST" in str(e):
            st.warning(f"Volume folder not found: {VOLUME_PATH}")
        else:
            st.error(f"Error reading gallery: {e}")

# ---------------------------------------------------------------------------
# TAB 2 — Cliente Table
# ---------------------------------------------------------------------------
with tab2:
    st.header("Cliente Table")
    st.caption(f"Tabela: `{CLIENTES_TABLE}`")

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
                        statement=f"SELECT * FROM {CLIENTES_TABLE} LIMIT 10",
                        wait_timeout="50s",
                    )
                    if response.status and response.status.state == StatementState.SUCCEEDED:
                        columns = [col.name for col in response.manifest.schema.columns]
                        rows = response.result.data_array or []
                        df = pd.DataFrame(rows, columns=columns)
                        st.dataframe(df, use_container_width=True)
                    else:
                        error_msg = (
                            response.status.error.message
                            if response.status and response.status.error
                            else "Unknown error"
                        )
                        st.error(f"Erro na consulta: {error_msg}")
            except Exception as e:
                st.error(f"Erro ao consultar: {e}")
        else:
            st.info("Clique em **Carregar dados** para executar a consulta.")

# ---------------------------------------------------------------------------
# TAB 3 — Dados Lakebase
# ---------------------------------------------------------------------------
with tab3:
    st.header("Dados Lakebase - Tabela Registros")

    with st.expander("🔍 Debug - Variáveis de Ambiente"):
        st.code(
            f"""
LAKEBASE_ENDPOINT: {os.environ.get('LAKEBASE_ENDPOINT', 'NÃO CONFIGURADO')}
PGHOST: {os.environ.get('PGHOST', 'NÃO CONFIGURADO')}
PGDATABASE: {os.environ.get('PGDATABASE', 'NÃO CONFIGURADO')}
PGPORT: {os.environ.get('PGPORT', 'NÃO CONFIGURADO')}
PGUSER: {os.environ.get('PGUSER', 'NÃO CONFIGURADO')}
PGSSLMODE: {os.environ.get('PGSSLMODE', 'NÃO CONFIGURADO')}
DATABRICKS_CLIENT_ID: {os.environ.get('DATABRICKS_CLIENT_ID', 'NÃO CONFIGURADO')}
DATABRICKS_WAREHOUSE_ID: {os.environ.get('DATABRICKS_WAREHOUSE_ID', 'NÃO CONFIGURADO')}
VOLUME_PATH: {VOLUME_PATH}
CLIENTES_TABLE: {CLIENTES_TABLE}
            """.strip()
        )

    endpoint = os.environ.get("LAKEBASE_ENDPOINT", "")
    pg_host = os.environ.get("PGHOST", "")
    pg_user = os.environ.get("PGUSER") or os.environ.get("DATABRICKS_CLIENT_ID", "")

    if not all([endpoint, pg_host, pg_user]):
        st.error(
            "❌ Variáveis de ambiente do Lakebase não configuradas. "
            "Anexe o recurso `postgres` ao app e use `LAKEBASE_ENDPOINT: valueFrom: postgres` no app.yaml."
        )
    else:
        st.subheader("➕ Adicionar Novo Registro")

        with st.form("new_record_form"):
            new_status = st.text_input(
                "Status", placeholder="Digite o status do novo registro"
            )
            submitted = st.form_submit_button("Adicionar Registro")

            if submitted:
                if not new_status:
                    st.error("Por favor, informe o status.")
                else:
                    try:
                        conn = get_lakebase_connection()
                        with conn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO registros (status) VALUES (%s) RETURNING id, status",
                                (new_status,),
                            )
                            new_record = cur.fetchone()
                            conn.commit()
                        conn.close()
                        st.success(
                            f"✅ Registro adicionado! ID: {new_record[0]}, Status: {new_record[1]}"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao adicionar registro: {e}")

        st.divider()
        st.subheader("📋 Registros Existentes")

        if st.button("🔄 Atualizar Lista", key="refresh_lakebase"):
            st.rerun()

        try:
            conn = get_lakebase_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT id, status FROM registros ORDER BY id")
                records = cur.fetchall()
            conn.close()

            if not records:
                st.info("Nenhum registro encontrado. Adicione um novo registro acima.")
            else:
                st.write(f"**Total de registros:** {len(records)}")

                for record in records:
                    record_id, record_status = record
                    col1, col2, col3 = st.columns([1, 3, 1])

                    with col1:
                        st.text(f"ID: {record_id}")

                    with col2:
                        new_status_value = st.text_input(
                            "Status",
                            value=record_status,
                            key=f"status_{record_id}",
                            label_visibility="collapsed",
                        )

                    with col3:
                        if st.button("💾 Salvar", key=f"update_{record_id}"):
                            if new_status_value != record_status:
                                try:
                                    conn = get_lakebase_connection()
                                    with conn.cursor() as cur:
                                        cur.execute(
                                            "UPDATE registros SET status = %s WHERE id = %s",
                                            (new_status_value, record_id),
                                        )
                                        conn.commit()
                                    conn.close()
                                    st.success(f"✅ Registro {record_id} atualizado!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(
                                        f"❌ Erro ao atualizar registro {record_id}: {e}"
                                    )
                            else:
                                st.info("Nenhuma alteração detectada.")

                    st.divider()

        except Exception as e:
            st.error(f"❌ Erro ao conectar ao Lakebase: {e}")
            st.info(
                """
**Verifique:**
- Recurso `postgres` anexado ao app (App resources)
- `LAKEBASE_ENDPOINT` via `valueFrom: postgres` no app.yaml
- `databricks-sdk>=0.89.0` no requirements.txt
- Role do service principal criada no Lakebase
- Tabela `public.registros` existe e tem GRANTs para o SP
                """
            )

# ---------------------------------------------------------------------------
# TAB 4 — AI/BI Dashboard
# ---------------------------------------------------------------------------
with tab4:
    st.header("AI/BI Dashboard")
    
    if not DASHBOARD_ID:
        st.warning(
            "⚠️ Dashboard ID não configurado. "
            "Configure a variável DASHBOARD_ID no app.yaml."
        )
        st.info(
            "**Passo a passo para embedar o dashboard:**\n\n"
            "1. **Criar dashboard**: Crie um dashboard AI/BI no Databricks\n"
            "2. **Publicar**: Clique em 'Publish' no dashboard (obrigatório para embed)\n"
            "3. **Obter ID**: Copie o ID da URL após `/dashboards/`: `/dashboards/<ID>`\n"
            "4. **Compartilhar**: No dashboard, clique 'Share' e adicione o App ID (Service Principal)\n"
            "5. **Configurar app.yaml**: Cole o Dashboard ID na variável DASHBOARD_ID\n"
            "6. **Admin liberar**: Settings → Security → External access → Embed dashboards → "
            "Permitir `*.databricksapps.com`"
        )
    else:
        st.caption(f"Dashboard ID: `{DASHBOARD_ID}`")
        
        # Obter workspace host do ambiente
        workspace_host = os.environ.get("DATABRICKS_HOST", "")
        
        if not workspace_host:
            st.error(
                "❌ Variável de ambiente DATABRICKS_HOST não encontrada. "
                "Não é possível construir a URL do dashboard."
            )
        else:
            # Construir URL do dashboard embedado
            # Remove protocolo se existir
            if workspace_host.startswith("https://"):
                workspace_host = workspace_host[8:]
            elif workspace_host.startswith("http://"):
                workspace_host = workspace_host[7:]
            
            # Remove trailing slash
            workspace_host = workspace_host.rstrip("/")
            
            # Construir URL completa para embed (usar /embed/dashboardsv3/ não /sql/dashboards/)
            dashboard_url = f"https://{workspace_host}/embed/dashboardsv3/{DASHBOARD_ID}"
            
            # Mostrar informações do dashboard
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.info(f"📊 Dashboard: `{DASHBOARD_ID}`")
            
            with col2:
                # Botão para abrir em nova aba
                st.link_button(
                    "🔗 Abrir Dashboard",
                    dashboard_url,
                    use_container_width=True
                )
            
            st.markdown("---")
            
            # Tentar embed direto (pode não funcionar devido a X-Frame-Options)
            st.warning(
                "⚠️ **Nota sobre Embed:**\n\n"
                "Dashboards do Databricks têm restrições de segurança que podem impedir "
                "o carregamento em iframes. Se o dashboard não aparecer abaixo, "
                "use o botão 'Abrir Dashboard' acima para visualizá-lo em uma nova aba."
            )
            
            # Tentar iframe com permissões
            iframe_html = f"""
            <style>
                .dashboard-container {{
                    width: 100%;
                    height: 800px;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    overflow: hidden;
                    background: #f5f5f5;
                }}
                .dashboard-iframe {{
                    width: 100%;
                    height: 100%;
                    border: none;
                }}
            </style>
            <div class="dashboard-container">
                <iframe 
                    class="dashboard-iframe"
                    src="{dashboard_url}"
                    sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
                    loading="lazy"
                ></iframe>
            </div>
            """
            
            st.components.v1.html(iframe_html, height=820, scrolling=True)
