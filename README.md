# Tech Radar & Rastreador de Candidaturas (Servidor MCP)

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-2.3.0-8A2BE2?style=for-the-badge)
![SQLite](https://img.shields.io/badge/SQLite-Local_DB-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![HTTPX](https://img.shields.io/badge/HTTPX-Async_Client-2B5B84?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-MVP_Funcional-2EA44F?style=for-the-badge)

## Sobre o Projeto

Este projeto foi desenvolvido como **entrega de encerramento do módulo de Claude** do curso de **Inteligência Artificial da Ada Tech**. O desafio proposto consistiu na construção de um servidor **Model Context Protocol (MCP)** em Python conectado ao **Claude Desktop** via transporte `stdio`, integrando ferramentas locais a APIs externas e conectores nativos para resolver um problema prático de tema livre.

Mais do que um exercício acadêmico, a aplicação foi projetada para atender a uma necessidade real da minha **transição de carreira para a área de Tecnologia (Desenvolvimento Back-End Júnior e Automação/RPA)**: centralizar a busca de oportunidades tech, avaliar automaticamente a aderência das vagas ao meu perfil técnico e eliminar a perda de controle sobre processos seletivos espalhados por múltiplas plataformas (Gupy, Eureca, LinkedIn, Indeed, Pandapé, entre outras).

---

## O que o Sistema Resolve

Durante a busca ativa por recolocação, dois gargalos são recorrentes: o tempo gasto filtrando vagas desalinhadas com a stack atual e a dificuldade de acompanhar datas de inscrição, canais utilizados e prazos de testes técnicos. O **Tech Radar MCP** transforma o Claude Desktop em um assistente operacional de carreira por meio de três pilares:

1. **Contexto Profissional Dinâmico:** O servidor disponibiliza meu resumo profissional, formação e projetos de portfólio diretamente para o modelo, permitindo diagnósticos reais de compatibilidade (*gap analysis*) sem alucinações.
2. **Prospecção em APIs Públicas:** Consulta oportunidades reais de tecnologia em tempo real, aplicando filtros por palavras-chave e stack.
3. **Rastreabilidade & Relatórios de Follow-up:** Persiste cada candidatura em um banco de dados relacional local (**SQLite**), calcula há quantos dias a inscrição foi realizada e exporta relatórios consolidados em Markdown para acompanhamento contínuo.

---

## Arquitetura e Ferramentas (`@mcp.tool`)

O servidor (`server.py`) utiliza o SDK oficial `mcp[cli]==2.3` e expõe **6 ferramentas customizadas** para o Claude Desktop:

| Módulo | Ferramenta | Descrição Técnica |
| :--- | :--- | :--- |
| **Perfil** | `obter_meu_perfil` | Lê dinamicamente o arquivo `data/meu_perfil.md` com stack, certificações e projetos para comparação de requisitos. |
| **Prospecção** | `buscar_vagas_tech` | Consulta a API pública **Remotive** (`software-dev`) filtrando vagas recentes por palavra-chave no título, tags e descrição. |
| **Prospecção** | `buscar_vagas_internacionais` | Consulta a API pública **Arbeitnow** para mapear vagas remotas e internacionais por título e tags técnicas. |
| **Histórico** | `registrar_candidatura` | Insere uma nova candidatura no banco `data/candidaturas.db` (empresa, cargo, plataforma, data, status, link e observações). |
| **Histórico** | `atualizar_status_candidatura` | Atualiza o estágio do processo (*Inscrita*, *Teste Técnico*, *Entrevista RH*, *Entrevista Técnica*, *Aprovada*, *Reprovada*) e registra notas com data. |
| **Relatórios** | `gerar_relatorio_candidaturas` | Consulta o SQLite com filtros opcionais, calcula dias corridos desde a inscrição e salva uma tabela em `relatorios/relatorio_candidaturas.md`. |

---

## Estrutura de Diretórios

```text
tech_radar_mcp/
├── .venv/                          # Ambiente virtual Python isolado
├── data/
│   ├── candidaturas.db             # Banco de dados SQLite (gerado automaticamente)
│   └── meu_perfil.md               # Base de conhecimento com stack, formação e projetos
├── relatorios/
│   └── relatorio_candidaturas.md   # Relatório Markdown gerado sob demanda
├── .gitignore                      # Proteção de dados sensíveis (*.db, relatórios e .venv)
├── README.md                       # Documentação do projeto
├── requirements.txt                # Dependências fixadas do ambiente
└── server.py                       # Servidor MCP e implementação das tools
```

---

## Como Executar Localmente

### 1. Clonar o repositório e configurar o ambiente virtual
```powershell
git clone <URL_DO_SEU_REPOSITORIO>
cd tech_radar_mcp

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Personalizar o perfil profissional
Edite o arquivo `data/meu_perfil.md` com suas tecnologias, experiências e objetivos de carreira.

### 3. Registrar o servidor no Claude Desktop
No **Claude Desktop**, acesse **Configurações → Aplicativo para desktop → Extensões → Gerenciar** para abrir o `claude_desktop_config.json` e adicione a configuração abaixo apontando para os caminhos absolutos da sua `.venv` e do `server.py`:

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

Reinicie completamente o Claude Desktop pela bandeja do sistema para carregar o conector `tech-radar-vagas`.

---

## Exemplos de Uso no Claude Desktop

* **Análise de Aderência (Busca + Perfil):**
  > *"Usa o Tech Radar para buscar vagas recentes de Python e compara os requisitos com o meu perfil."*
* **Registro Rápido de Inscrição:**
  > *"Registra que me inscrevi hoje na plataforma Gupy para Desenvolvedora Python Júnior na empresa X, com prazo de teste técnico até sexta-feira."*
* **Atualização de Processo Seletivo:**
  > *"Atualiza minha candidatura da empresa X para 'Teste Técnico Enviado'."*
* **Geração de Relatório de Acompanhamento:**
  > *"Gera meu relatório completo de candidaturas e destaca quais estão há mais de 7 dias sem atualização."*
* **Orquestração com Conectores Nativos (Google Workspace):**
  > *"Verifica meus e-mails recentes da Gupy e Eureca no Gmail e registra no Tech Radar as candidaturas que ainda não estão no meu histórico."*

---

## Escopo Atual & Roadmap de Melhorias Futuras

Por ter sido concebido e entregue dentro de um **prazo curto** para a finalização do módulo na Ada Tech, o projeto foi estruturado como um **MVP (Produto Mínimo Viável)** enxuto, funcional e livre de dependências externas pagas.

Como esta ferramenta será utilizada ativamente na minha jornada de transição de carreira para encontrar e gerenciar vagas reais, as próximas evoluções planejadas incluem:

- [ ] **Integração com Portais Brasileiros e Vagas Júnior:** Adicionar coletores/APIs focados no mercado brasileiro (como repositórios de vagas do GitHub `backend-br`, `qa-brasil` e agregadores nacionais) para ampliar o volume de oportunidades de nível Júnior no Brasil.
- [ ] **Sistema de Pontuação de Match (Scoring):** Implementar um algoritmo de ranqueamento em Python que calcule uma nota percentual de compatibilidade entre a descrição da vaga e as palavras-chave do `meu_perfil.md` antes mesmo de exibir os resultados.
- [ ] **Alertas Automáticos de Follow-up e Prazos:** Criar uma ferramenta de verificação proativa que identifique candidaturas paradas há mais de 7 ou 14 dias e sugira mensagens personalizadas de acompanhamento para recrutadores.
- [ ] **Exportação Multi-formato (CSV / Excel):** Expandir o módulo de relatórios para exportar planilhas `.csv` e `.xlsx` formatadas, além do Markdown atual.
- [ ] **Validação Rigorosa com Pydantic v2 & Testes Unitários:** Refatorar os schemas de entrada das *tools* utilizando modelos `Pydantic v2` e adicionar uma suíte de testes automatizados com `Pytest` para garantir a integridade das operações no SQLite.

---

## Tecnologias Utilizadas

* **Python 3.13**
* **MCP SDK (`mcp[cli]==2.3`)** — Comunicação via protocolo `stdio` entre ferramentas locais e o Claude Desktop
* **HTTPX** — Requisições assíncronas para consumo de APIs REST
* **SQLite3** — Persistência relacional leve para histórico de candidaturas

---

## Autora

**Tayga Rayanne**  
Desenvolvedora Back-End & Automação/RPA | Graduanda em Banco de Dados | Tecnóloga em Análise e Desenvolvimento de Sistemas
