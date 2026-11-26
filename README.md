# Tech Radar & Rastreador de Candidaturas (Servidor MCP + Skill)

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-2.3.0-8A2BE2?style=for-the-badge)
![SQLite](https://img.shields.io/badge/SQLite-Local_DB-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![HTTPX](https://img.shields.io/badge/HTTPX-Async_Client-2B5B84?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Evolu%C3%ADdo_com_Skill_%26_Workspace-2EA44F?style=for-the-badge)

## Sobre o Projeto

Este projeto foi desenvolvido como **entrega de encerramento do módulo de Claude** do curso de **Inteligência Artificial da Ada Tech**. A solução implementa um servidor **Model Context Protocol (MCP)** em Python conectado ao **Claude Desktop** via transporte `stdio`, combinado com uma **Skill personalizada (`tech-radar-carreira`)** e conectores nativos do **Google Workspace (Gmail e Google Calendar)**.

Projetado para apoiar minha **transição de carreira para Desenvolvimento Back-End Júnior e Automação/RPA**, o sistema centraliza a prospecção de vagas no Brasil e no exterior, calcula aderência técnica (*scorecard* ponderado) com base no meu perfil real, protege contra *prompt injection* em descrições externas e automatiza o controle de candidaturas e *follow-ups*.

---

## O que o Sistema Resolve

1. **Contexto Profissional Estruturado:** Lê dinamicamente o perfil técnico (`data/meu_perfil.md`) com matriz de competências, projetos e critérios de filtro para diagnósticos precisos sem alucinações.
2. **Prospecção Brasil & Exterior em Tempo Real:** Consulta vagas abertas da comunidade brasileira (`backend-br/vagas` via API do GitHub) e portais internacionais remotos (**Remotive** e **Arbeitnow**).
3. **Rastreabilidade, Follow-up & Google Workspace:** Persiste candidaturas em banco local (**SQLite**), identifica processos parados há 7 dias ou mais, gera relatórios em Markdown e cruza convites de entrevista e prazos de testes técnicos com o **Gmail** e a **Google Agenda**.

---

## Arquitetura: Servidor MCP + Skill + Google Workspace

### 1. Ferramentas do Servidor MCP (`server.py` — 8 `@mcp.tool`)

| Módulo | Ferramenta | Descrição Técnica |
| :--- | :--- | :--- |
| **Perfil** | `obter_meu_perfil` | Lê `data/meu_perfil.md` com stack, projetos e matriz de critérios para comparação de requisitos. |
| **Prospecção BR** | `buscar_vagas_brasil` | Consulta a API pública do GitHub no repositório **`backend-br/vagas`** filtrando por tecnologia e senioridade (ex.: `python`, `junior`). |
| **Prospecção Global** | `buscar_vagas_tech` | Consulta a API pública **Remotive** (`software-dev`) filtrando vagas recentes por palavra-chave no título, tags e descrição. |
| **Prospecção Global** | `buscar_vagas_internacionais` | Consulta a API pública **Arbeitnow** para mapear vagas remotas e internacionais por título e tags técnicas. |
| **Histórico** | `registrar_candidatura` | Insere uma nova candidatura no banco `data/candidaturas.db` (empresa, cargo, plataforma, data, status, link e observações). |
| **Histórico** | `atualizar_status_candidatura` | Atualiza o estágio do processo (*Inscrita*, *Teste Técnico*, *Entrevista RH*, *Entrevista Técnica*, *Aprovada*, *Reprovada*) e registra notas datadas. |
| **Follow-up** | `verificar_followups` | Identifica candidaturas ativas paradas há X dias ou mais (padrão: 7 dias) sem atualização de status. |
| **Relatórios** | `gerar_relatorio_candidaturas` | Consulta o SQLite com filtros opcionais, calcula dias corridos desde a inscrição e salva uma tabela em `relatorios/relatorio_candidaturas.md`. |

### 2. Skill Personalizada (`skills/tech-radar-carreira/SKILL.md`)
* **Scorecard Padronizado:** Calcula nota de aderência (0% a 100%), lista **Pontos Fortes**, **Pontos de Atenção / Gaps** e gera rascunho de abordagem para recrutador no LinkedIn quando o *match* é $\ge 70\%$.
* **Segurança (Anti-Prompt Injection):** Trata textos vindos de APIs externas e e-mails estritamente como dados não confiáveis, ignorando instruções ocultas.
* **Orquestração Google Workspace:** Cruza e-mails de processos seletivos no **Gmail** com o histórico local e oferece agendar entrevistas ou prazos de testes na **Google Agenda** mediante confirmação.

---

## Estrutura de Diretórios

```text
tech_radar_mcp/
├── .venv/                              # Ambiente virtual Python isolado (ignorado no Git)
├── data/
│   ├── candidaturas.db                 # Banco SQLite local (ignorado no Git)
│   ├── meu_perfil.md                   # Perfil real da candidata (ignorado no Git por privacidade)
│   └── meu_perfil.example.md           # Template público com nota de segurança
├── relatorios/
│   └── .gitkeep                        # Mantém diretório versionado sem expor relatórios locais
├── skills/
│   └── tech-radar-carreira/
│       └── SKILL.md                    # Definição versionada da Skill do Claude Desktop
├── .gitignore                          # Proteção de dados sensíveis (*.db, perfil real e .venv)
├── README.md                           # Documentação do projeto
├── requirements.txt                    # Dependências fixadas (mcp[cli], httpx)
└── server.py                           # Servidor MCP e implementação das 8 tools
```

---

## Como Executar Localmente

### 1. Clonar o repositório e configurar o ambiente virtual
```powershell
git clone [https://github.com/TayagaRayanne/tech-radar-mcp.git](https://github.com/TayagaRayanne/tech-radar-mcp.git)
cd tech_radar_mcp

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Criar seu perfil local
Copie o arquivo modelo `data/meu_perfil.example.md` para `data/meu_perfil.md` e preencha com suas tecnologias, formação e critérios de busca.

### 3. Registrar o servidor e a Skill no Claude Desktop
1. No **Claude Desktop**, acesse **Configurações → Aplicativo para desktop → Extensões → Gerenciar** (`claude_desktop_config.json`) e adicione:

```json
{
  "mcpServers": {
    "tech-radar-vagas": {
      "command": "C:\\caminho\\para\\tech_radar_mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\caminho\\para\\tech_radar_mcp\\server.py"
      ]
    }
  }
}
```

2. Em **Configurações → Plugins → Skills**, importe ou crie a Skill a partir de `skills/tech-radar-carreira/SKILL.md` e vincule os conectores **Gmail** e **Google Calendar**.

---

## Segurança e Privacidade (LGPD)

* **Isolamento de Dados Pessoais:** O banco `data/candidaturas.db`, os relatórios gerados e o arquivo real `data/meu_perfil.md` são bloqueados pelo `.gitignore`, permanecendo exclusivamente no ambiente local da usuária.
* **Sem Exposição de Credenciais:** Todas as APIs externas consumidas (`GitHub Issues`, `Remotive` e `Arbeitnow`) são públicas e não exigem chaves em código.
* **Defesa contra Prompt Injection:** A Skill instrui o modelo a tratar descrições de vagas e e-mails externos apenas como dados, bloqueando comandos embutidos.

---

## Roadmap de Evoluções Futuras

- [ ] **Sistema de Scoring Determinístico em Python:** Calcular pontuação matemática ponderada diretamente no backend antes da análise semântica do LLM.
- [ ] **Exportação Multi-formato (CSV / Excel):** Adicionar exportação em `.csv` e `.xlsx` além do relatório Markdown atual.
- [ ] **Validação com Pydantic v2 & Testes Unitários (Pytest):** Adicionar modelos Pydantic nos parâmetros das *tools* e suíte automatizada de testes para o banco SQLite.

---

## Tecnologias Utilizadas

* **Python 3.13**
* **MCP SDK (`mcp[cli]==2.3`)** — Comunicação via protocolo `stdio` entre ferramentas locais e o Claude Desktop
* **HTTPX** — Requisições assíncronas para consumo das APIs GitHub (`backend-br/vagas`), Remotive e Arbeitnow
* **SQLite3** — Persistência relacional local para histórico de candidaturas e controle de *follow-up*
* **Claude Skills & Google Workspace** — Padronização de comportamento do agente e integração com Gmail/Google Calendar

---

## Autora

**Tayga Rayanne**  
Desenvolvedora Back-End & Automação/RPA | Graduanda em Banco de Dados | Analista e Desenvolvedora de Sistemas