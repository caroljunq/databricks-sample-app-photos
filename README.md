# Demo Energia Album — Databricks Apps

Workshop / sample de um **Databricks App** em Streamlit que demonstra leitura/escrita de dados no Databricks e, opcionalmente, embed de dashboard:

| Aba | O que faz | Fonte de dados | Seção do guia |
|-----|-----------|----------------|---------------|
| **Photo Album** | Upload e galeria de imagens | Unity Catalog **Volume** | Seção 1 |
| **Cliente Table** | Consulta de clientes | Tabela Delta via **SQL Warehouse** | Seção 1 |
| **Dados Lakebase** | CRUD de registros (status) | **Lakebase Autoscaling** (Postgres) | Seção 2 (opcional) |
| **AI/BI Dashboard** | Embed / link de dashboard | Dashboard AI/BI | Seção 3 (opcional) |

---

## Como começar

Siga o passo a passo no notebook:

**[`1-guia-passo-a-passo.ipynb`](./1-guia-passo-a-passo.ipynb)**

- **Seção 1** — Unity Catalog + SQL Warehouse + App + deploy (obrigatória)
- **Seção 2** — Integração com Lakebase (opcional)
- **Seção 3** — Embed de AI/BI Dashboards no Databricks App (opcional)

Substitua os placeholders `xxxxxxx` pelos IDs e paths do seu workspace antes do deploy.

---

## Dados usados pelo app

### 1. Volume (Photo Album)

- Path típico: `/Volumes/<catalog>/default/fotos`
- Configurado em `VOLUME_PATH` no `app/app.yaml`
- Armazena imagens enviadas pelo usuário (jpg/png/gif)

### 2. Tabela Delta `clientes` (Cliente Table)

- Formato típico: `<catalog>.default.clientes`
- Configurado em `CLIENTES_TABLE` no `app/app.yaml`
- Colunas de exemplo: `id`, `nome`, `cidade`, `segmento`
- Lida via SQL Warehouse (`DATABRICKS_WAREHOUSE_ID`)

### 3. Tabela Postgres `registros` (Dados Lakebase — Seção 2, opcional)

- Database: `databricks_postgres` (padrão do Lakebase Autoscaling)
- Schema: `public`
- Colunas: `id` (serial), `status` (text)
- Autenticação: service principal do app + token OAuth (`w.postgres.generate_database_credential`)

### 4. Dashboard AI/BI (Seção 3, opcional)

- Configurado em `DASHBOARD_ID` no `app/app.yaml`
- Usado na aba **AI/BI Dashboard** (iframe / link)
- Exige: dashboard **publicado**, share com o SP do app, e política de embedding liberada no workspace (ver Seção 3 do guia)

> No repositório, valores sensíveis (IDs de warehouse, paths reais, etc.) estão mascarados com `xxxxxxx` para commit seguro.

---

## Estrutura do repositório

```text
.
├── 1-guia-passo-a-passo.ipynb   # Guia completo de deploy (comece por aqui)
├── README.md                    # Este arquivo
├── LICENSE
├── .gitignore
└── app/                         # Código do Databricks App (sync/deploy)
    ├── app.py                   # App Streamlit (4 abas)
    ├── app.yaml                 # Comando, env vars e permissions
    ├── requirements.txt         # Dependências Python do app
    └── manifest.yaml            # Metadados do app
```

### Para que serve cada arquivo

| Arquivo | Função |
|---------|--------|
| `1-guia-passo-a-passo.ipynb` | Runbook do workshop: Seção 1 (App/UC/SQL), Seção 2 (Lakebase opcional), Seção 3 (embed AI/BI opcional) |
| `app/app.py` | Código Streamlit: Photo Album, Cliente Table, Dados Lakebase e AI/BI Dashboard |
| `app/app.yaml` | Define como o app sobe (`streamlit run app.py`), variáveis de ambiente e permissions genéricas do SP |
| `app/requirements.txt` | Dependências: `streamlit`, `databricks-sdk>=0.89.0`, `psycopg2-binary` |
| `app/manifest.yaml` | Nome e descrição do app |
| `.gitignore` | Ignora `.databricks/`, venv, `.env`, etc. |

---

## Variáveis de ambiente (`app/app.yaml`)

| Variável | Obrigatória? | Uso |
|----------|--------------|-----|
| `DATABRICKS_WAREHOUSE_ID` | Sim (Seção 1) | Consultas da aba Cliente Table |
| `VOLUME_PATH` | Sim (Seção 1) | Path do volume de fotos |
| `CLIENTES_TABLE` | Sim (Seção 1) | Tabela Delta de clientes |
| `LAKEBASE_ENDPOINT` | Não (Seção 2) | `valueFrom: postgres` — endpoint Lakebase |
| `DASHBOARD_ID` | Não (Seção 3) | ID do dashboard AI/BI para embed |

Variáveis **injetadas pelo runtime** quando o recurso `postgres` está anexado ao app (não colocar no yaml):

`PGHOST`, `PGDATABASE`, `PGPORT`, `PGUSER`, `PGSSLMODE`, `DATABRICKS_CLIENT_ID`

Detalhes de como obter cada valor estão no guia `1-guia-passo-a-passo.ipynb`.

---

## Pré-requisitos rápidos

1. Databricks CLI autenticado no workspace
2. Permissão para criar Apps e conceder acessos (idealmente workspace admin)
3. SQL Warehouse disponível
4. (Opcional) Projeto Lakebase Autoscaling — Seção 2 do guia
5. (Opcional) Dashboard AI/BI publicado + permissão de embedding — Seção 3 do guia

---

## Licença

Veja [`LICENSE`](./LICENSE).
