import sqlite3
from datetime import datetime
from pathlib import Path
import httpx
from mcp.server.mcpserver import MCPServer

# Caminhos absolutos baseados na localização do server.py
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RELATORIOS_DIR = BASE_DIR / "relatorios"
DB_PATH = DATA_DIR / "candidaturas.db"
PERFIL_PATH = DATA_DIR / "meu_perfil.md"

# Garante que os diretórios existam
DATA_DIR.mkdir(parents=True, exist_ok=True)
RELATORIOS_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "TechRadarMCP/1.1 (AdaTech-ModuloClaude)"

# Inicializa o servidor MCP
mcp = MCPServer("tech-radar-vagas")


def inicializar_banco() -> None:
    """Cria a tabela de candidaturas no SQLite caso ainda não exista."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS candidaturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa TEXT NOT NULL,
                cargo TEXT NOT NULL,
                plataforma TEXT NOT NULL,
                data_inscricao TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Inscrita',
                link TEXT,
                observacoes TEXT,
                ultima_atualizacao TEXT NOT NULL
            )
            """
        )
        conn.commit()


inicializar_banco()


# =====================================================================
# MÓDULO 0: PERFIL PROFISSIONAL DA CANDIDATA
# =====================================================================

@mcp.tool()
def obter_meu_perfil() -> str:
    """
    Lê e retorna o perfil profissional, stack técnica, formação e projetos da usuária
    a partir do arquivo local 'data/meu_perfil.md'.
    Use sempre que precisar comparar requisitos de vagas com o perfil da candidata.
    """
    if not PERFIL_PATH.exists():
        return (
            "Arquivo 'data/meu_perfil.md' não encontrado. "
            "Peça para a usuária criar o arquivo com seu resumo profissional."
        )
    return PERFIL_PATH.read_text(encoding="utf-8")


# =====================================================================
# MÓDULO 1: BUSCA DE VAGAS EM APIS EXTERNAS (BRASIL & INTERNACIONAL)
# =====================================================================

@mcp.tool()
async def buscar_vagas_brasil(
    palavra_chave: str = "python",
    senioridade: str = "junior",
    limite: int = 5
) -> str:
    """
    Busca vagas abertas no mercado brasileiro através da API pública do GitHub
    no repositório oficial da comunidade 'backend-br/vagas', filtrando por
    tecnologia (ex: 'python', 'fastapi', 'sql', 'backend') e senioridade (ex: 'junior', 'pleno', '').
    """
    url = "https://api.github.com/repos/backend-br/vagas/issues"
    params = {"state": "open", "per_page": 50}
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            issues = response.json()
        except httpx.HTTPError as e:
            return f"Erro ao consultar vagas brasileiras no GitHub (backend-br): {str(e)}"

    termo_tech = palavra_chave.strip().lower()
    termo_nivel = senioridade.strip().lower()

    vagas_filtradas = []
    for item in issues:
        # Ignora Pull Requests caso venham na listagem
        if "pull_request" in item:
            continue

        titulo = item.get("title", "").lower()
        corpo = (item.get("body") or "").lower()
        labels = [lbl.get("name", "").lower() for lbl in item.get("labels", [])]
        texto_completo = f"{titulo} {' '.join(labels)} {corpo}"

        bate_tech = not termo_tech or (termo_tech in texto_completo)
        bate_nivel = not termo_nivel or (termo_nivel in texto_completo)

        if bate_tech and bate_nivel:
            vagas_filtradas.append(item)

    if not vagas_filtradas:
        return (
            f"Nenhuma vaga aberta encontrada em 'backend-br/vagas' para "
            f"tecnologia='{palavra_chave}' e senioridade='{senioridade}'."
        )

    linhas = [
        f"### Vagas no Brasil (backend-br/vagas) — Filtro: `{palavra_chave}` | `{senioridade or 'Todas'}`:\n"
    ]
    for vaga in vagas_filtradas[:limite]:
        titulo = vaga.get("title", "Sem título")
        labels_nomes = [lbl.get("name", "") for lbl in vaga.get("labels", [])[:6]]
        tags = ", ".join(labels_nomes) or "Sem etiquetas"
        data_pub = vaga.get("created_at", "")[:10]
        link = vaga.get("html_url", "")
        resumo = (vaga.get("body") or "").strip().replace("\r\n", " ").replace("\n", " ")[:220]

        linhas.append(
            f"- **{titulo}**\n"
            f"  - Etiquetas: {tags}\n"
            f"  - Publicada em: {data_pub}\n"
            f"  - Resumo: {resumo}...\n"
            f"  - Link: {link}"
        )

    return "\n".join(linhas)


@mcp.tool()
async def buscar_vagas_tech(palavra_chave: str = "python", limite: int = 5) -> str:
    """
    Busca vagas recentes de desenvolvimento de software na API pública Remotive
    filtrando rigorosamente pela palavra-chave no título ou tags da vaga
    (ex: 'python', 'backend', 'rpa', 'junior', 'api').
    """
    url = "https://remotive.com/api/remote-jobs"
    params = {"category": "software-dev", "search": palavra_chave}

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(url, params=params, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            dados = response.json()
        except httpx.HTTPError as e:
            return f"Erro ao consultar a API Remotive: {str(e)}"

    todas_vagas = dados.get("jobs", [])
    termo = palavra_chave.strip().lower()

    vagas_filtradas = [
        v for v in todas_vagas
        if termo in v.get("title", "").lower()
        or any(termo in tag.lower() for tag in v.get("tags", []))
        or termo in v.get("description", "").lower()
    ]

    if not vagas_filtradas:
        return f"Nenhuma vaga específica encontrada na Remotive para '{palavra_chave}'."

    linhas = [f"### Vagas de Tecnologia encontradas (Remotive) para '{palavra_chave}':\n"]
    for vaga in vagas_filtradas[:limite]:
        titulo = vaga.get("title", "Sem título")
        empresa = vaga.get("company_name", "Não informada")
        local = vaga.get("candidate_required_location", "Remoto")
        tags = ", ".join(vaga.get("tags", [])[:5]) or "Não informadas"
        data_pub = vaga.get("publication_date", "")[:10]
        link = vaga.get("url", "")

        linhas.append(
            f"- **{titulo}** | Empresa: {empresa}\n"
            f"  - Tags: {tags}\n"
            f"  - Região: {local} | Publicada em: {data_pub}\n"
            f"  - Link: {link}"
        )

    return "\n".join(linhas)


@mcp.tool()
async def buscar_vagas_internacionais(termo: str = "python", limite: int = 5) -> str:
    """
    Consulta a API pública Arbeitnow para buscar oportunidades de desenvolvimento
    e automação remotas ou internacionais filtrando por título ou tags.
    """
    url = "https://www.arbeitnow.com/api/job-board-api"

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(url, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            dados = response.json()
        except httpx.HTTPError as e:
            return f"Erro ao consultar a API Arbeitnow: {str(e)}"

    todas_vagas = dados.get("data", [])
    termo_lower = termo.lower()

    filtradas = [
        v for v in todas_vagas
        if termo_lower in v.get("title", "").lower()
        or any(termo_lower in tag.lower() for tag in v.get("tags", []))
    ]

    if not filtradas:
        return f"Nenhuma vaga encontrada na Arbeitnow para '{termo}'."

    linhas = [f"### Vagas encontradas (Arbeitnow) para '{termo}':\n"]
    for vaga in filtradas[:limite]:
        titulo = vaga.get("title", "Sem título")
        empresa = vaga.get("company_name", "Não informada")
        remoto = "Remoto" if vaga.get("remote") else "Híbrido/Presencial"
        tags = ", ".join(vaga.get("tags", [])[:4])
        link = vaga.get("url", "")

        linhas.append(
            f"- **{titulo}** ({empresa}) | Modelo: {remoto}\n"
            f"  - Tags: {tags}\n"
            f"  - Link: {link}"
        )

    return "\n".join(linhas)


# =====================================================================
# MÓDULO 2: HISTÓRICO, FOLLOW-UPS E RELATÓRIOS (SQLITE)
# =====================================================================

@mcp.tool()
def registrar_candidatura(
    empresa: str,
    cargo: str,
    plataforma: str,
    data_inscricao: str = "",
    status: str = "Inscrita",
    link: str = "",
    observacoes: str = ""
) -> str:
    """
    Registra uma nova candidatura no banco de dados local SQLite para histórico e acompanhamento.
    """
    hoje = datetime.now().strftime("%Y-%m-%d")
    data_final = data_inscricao.strip() if data_inscricao.strip() else hoje

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO candidaturas (
                empresa, cargo, plataforma, data_inscricao, status, link, observacoes, ultima_atualizacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                empresa.strip(),
                cargo.strip(),
                plataforma.strip(),
                data_final,
                status.strip(),
                link.strip(),
                observacoes.strip(),
                hoje
            )
        )
        novo_id = cursor.lastrowid
        conn.commit()

    return (
        f"Candidatura registrada com sucesso! (ID #{novo_id})\n"
        f"- **Empresa:** {empresa}\n"
        f"- **Cargo:** {cargo}\n"
        f"- **Plataforma:** {plataforma}\n"
        f"- **Data de Inscrição:** {data_final}\n"
        f"- **Status:** {status}"
    )


@mcp.tool()
def atualizar_status_candidatura(
    identificador: str,
    novo_status: str,
    nova_observacao: str = ""
) -> str:
    """
    Atualiza o status e/ou observações de uma candidatura existente pelo ID ou nome da empresa.
    """
    hoje = datetime.now().strftime("%Y-%m-%d")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if identificador.isdigit():
            registro = conn.execute("SELECT * FROM candidaturas WHERE id = ?", (int(identificador),)).fetchone()
        else:
            registro = conn.execute(
                "SELECT * FROM candidaturas WHERE LOWER(empresa) LIKE ? ORDER BY id DESC LIMIT 1",
                (f"%{identificador.lower()}%",)
            ).fetchone()

        if not registro:
            return f"Nenhuma candidatura encontrada para o identificador '{identificador}'."

        obs_final = registro["observacoes"] or ""
        if nova_observacao.strip():
            obs_final = f"{obs_final} | [{hoje}] {nova_observacao.strip()}".strip(" |")

        conn.execute(
            """
            UPDATE candidaturas
            SET status = ?, observacoes = ?, ultima_atualizacao = ?
            WHERE id = ?
            """,
            (novo_status.strip(), obs_final, hoje, registro["id"])
        )
        conn.commit()

    return (
        f"Candidatura **#{registro['id']} ({registro['empresa']} - {registro['cargo']})** atualizada!\n"
        f"- **Novo Status:** {novo_status}\n"
        f"- **Observações:** {obs_final or 'Nenhuma'}"
    )


@mcp.tool()
def verificar_followups(dias_sem_resposta: int = 7) -> str:
    """
    Verifica candidaturas ativas no banco SQLite que estão há 'dias_sem_resposta' ou mais
    sem atualização de status, ajudando a identificar onde fazer follow-up com recrutadores.
    """
    status_encerrados = ("aprovada", "reprovada", "desistência", "encerrada", "cancelada")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        registros = conn.execute(
            "SELECT * FROM candidaturas ORDER BY ultima_atualizacao ASC, id ASC"
        ).fetchall()

    if not registros:
        return "Nenhuma candidatura cadastrada no banco de dados ainda."

    hoje_dt = datetime.now()
    pendentes = []

    for r in registros:
        if r["status"].strip().lower() in status_encerrados:
            continue

        try:
            dt_ref = datetime.strptime(r["ultima_atualizacao"], "%Y-%m-%d")
            dias_parados = (hoje_dt - dt_ref).days
        except ValueError:
            continue

        if dias_parados >= dias_sem_resposta:
            pendentes.append((dias_parados, r))

    if not pendentes:
        return f"Nenhuma candidatura ativa está parada há {dias_sem_resposta} dias ou mais."

    linhas = [
        f"### Candidaturas pendentes de Follow-up (>= {dias_sem_resposta} dias sem atualização):\n"
    ]
    for dias_parados, r in pendentes:
        linhas.append(
            f"- **#{r['id']} {r['empresa']}** — {r['cargo']} ({r['plataforma']})\n"
            f"  - Status atual: `{r['status']}` | Parada há: **{dias_parados} dias** (última atualização: {r['ultima_atualizacao']})\n"
            f"  - Observações: {r['observacoes'] or 'Nenhuma'}"
        )

    return "\n".join(linhas)


@mcp.tool()
def gerar_relatorio_candidaturas(
    filtro_status: str = "",
    filtro_plataforma: str = "",
    salvar_arquivo: bool = True
) -> str:
    """
    Gera um relatório completo das candidaturas registradas no histórico, calculando
    quantos dias se passaram desde a inscrição e salvando um arquivo Markdown em 'relatorios/'.
    """
    query = "SELECT * FROM candidaturas WHERE 1=1"
    params = []

    if filtro_status.strip():
        query += " AND LOWER(status) LIKE ?"
        params.append(f"%{filtro_status.strip().lower()}%")

    if filtro_plataforma.strip():
        query += " AND LOWER(plataforma) LIKE ?"
        params.append(f"%{filtro_plataforma.strip().lower()}%")

    query += " ORDER BY data_inscricao DESC, id DESC"

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        registros = conn.execute(query, params).fetchall()

    if not registros:
        return "Nenhuma candidatura encontrada no histórico com os filtros informados."

    hoje_dt = datetime.now()
    agora_str = hoje_dt.strftime("%d/%m/%Y às %H:%M")

    linhas = [
        "# Relatório de Acompanhamento de Candidaturas",
        f"_Gerado em {agora_str} | Total encontrado: {len(registros)}_\n",
        "| ID | Data Inscrição | Dias | Empresa | Cargo | Plataforma | Status | Observações / Link |",
        "|---|---|---|---|---|---|---|---|"
    ]

    for r in registros:
        try:
            dt_insc = datetime.strptime(r["data_inscricao"], "%Y-%m-%d")
            dias_corridos = (hoje_dt - dt_insc).days
            dias_txt = f"{dias_corridos}d"
        except ValueError:
            dias_txt = "-"

        obs_e_link = []
        if r["observacoes"]:
            obs_e_link.append(r["observacoes"])
        if r["link"]:
            obs_e_link.append(f"[Link]({r['link']})")
        detalhes = " — ".join(obs_e_link) if obs_e_link else "-"

        linhas.append(
            f"| #{r['id']} | {r['data_inscricao']} | {dias_txt} | **{r['empresa']}** | "
            f"{r['cargo']} | {r['plataforma']} | `{r['status']}` | {detalhes} |"
        )

    relatorio_md = "\n".join(linhas)

    if salvar_arquivo:
        caminho_arquivo = RELATORIOS_DIR / "relatorio_candidaturas.md"
        caminho_arquivo.write_text(relatorio_md, encoding="utf-8")
        relatorio_md += f"\n\n> Arquivo salvo localmente em: `{caminho_arquivo}`"

    return relatorio_md


if __name__ == "__main__":
    mcp.run(transport="stdio")