# AB-hub By Aquiles_Bachira

**Sistema de Inteligência de Projectos e Controlo de Repositórios**

> Cada projecto tem uma história. O AB-hub garante que nenhuma se perde.  
> **Sabe o que construiu. Controla o que possui.**

Versão **0.1.0**

## Visão geral

O AB-hub é uma aplicação CLI local-first e apenas de leitura que descobre, inventaria, analisa, classifica e monitoriza todos os repositórios GitHub a que tem acesso autorizado (pessoais, privados e de organizações).

Funciona como um arquivo central de engenharia para nunca perder o rasto de projectos, tecnologias, histórico de actividade ou trabalho abandonado.

### Principais funcionalidades

- Descoberta de todos os repositórios acessíveis (proprietário / colaborador / organização)
- Detecção de tecnologias e dependências
- Inteligência de commits e actividade com pontuação explicável
- Persistência local em SQLite (funciona offline após a primeira sincronização)
- Análise incremental
- Filtragem, pesquisa, comparação e exportação (JSON / CSV / Markdown)
- Arquitectura totalmente modular e extensível

## Requisitos

- Python 3.12+
- Um Token de Acesso Pessoal do GitHub com os âmbitos adequados:
  - `repo` (para repositórios privados)
  - `read:org` (para repositórios de organizações)

## Instalação

```bash
# Clonar ou extrair o projecto
cd AB-hub

# Criar ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows

# Instalar
pip install -e ".[dev]"
```

## Início rápido

```bash
# Abrir o shell interactivo (permanece aberto até q + Enter)
ab-hub

# Dentro do shell:
#   autenticacao entrar
#   analisar
#   listar
#   q

# Ou comandos clássicos num só passo:
ab-hub autenticacao entrar

# Verificar ligação
ab-hub autenticacao estado

# 2. Descobrir e analisar repositórios
ab-hub analisar

# Opcional: incluir análise de vulnerabilidades
ab-hub analisar --security

# 3. Listar repositórios
ab-hub listar

# 4. Inspeccionar um projecto específico
ab-hub inspeccionar ver <nome-do-repo>

# 5. Actividade e segurança
ab-hub actividade
ab-hub abandonados
ab-hub seguranca resumo

# 6. Exportar
ab-hub exportar --format json
```

Ao executar `ab-hub` sem argumentos, é mostrado um ecrã inicial amigável com o estado e comandos rápidos.

## Comandos do CLI

| Comando | Descrição |
|---------|-------------|
| `ab-hub autenticacao entrar` | Guardar o token GitHub de forma segura |
| `ab-hub autenticacao estado` | Verificar o estado de autenticação |
| `ab-hub autenticacao sair` | Remover as credenciais guardadas |
| `ab-hub analisar` | Descobrir e analisar repositórios |
| `ab-hub analisar --incremental` | Processar apenas alterações |
| `ab-hub listar` | Listar repositórios (com filtros) |
| `ab-hub inspeccionar ver <nome>` | Inspecção detalhada de um repositório |
| `ab-hub tecnologias` | Visão geral de tecnologias |
| `ab-hub actividade <nome>` | Pontuação de actividade e classificação |
| `ab-hub abandonados` | Listar projectos possivelmente abandonados |
| `ab-hub comparar <a> <b>` | Comparar dois repositórios |
| `ab-hub relatorio gerar` | Gerar relatório resumido |
| `ab-hub exportar --format json\|csv\|markdown` | Exportar dados |
| `ab-hub seguranca analisar` | Análise de vulnerabilidades (OSV) |
| `ab-hub seguranca resumo` | Postura de segurança global |
| `ab-hub seguranca listar <repo>` | Vulnerabilidades de um repositório |

Os nomes em inglês (`auth`, `scan`, `list`, …) continuam a funcionar como aliases.

## Arquitectura

```
AB-hub CLI
    └── Núcleo da aplicação
            ├── Motor de descoberta
            ├── Motor de inteligência (Tech / Commits / Actividade)
            ├── Motor de controlo
            └── Repositório de dados (SQLite)
```

## Segurança

- Os tokens nunca são guardados na base de dados nem impressos nos logs.
- Preferência pelo keyring do sistema quando disponível.
- Apenas de leitura por desenho — nunca modifica repositórios remotos.
- Permissões mínimas necessárias.

## Monitorização de segurança

```bash
# Durante uma análise normal
ab-hub analisar --security

# Passagem dedicada de segurança
ab-hub seguranca analisar
ab-hub seguranca analisar meu-repo
ab-hub seguranca resumo
ab-hub seguranca listar meu-repo
```

Os resultados são guardados localmente e incluídos nos relatórios. Níveis de gravidade: CRITICAL, HIGH, MEDIUM, LOW.

## Desenvolvimento

```bash
ruff check .
ruff format .
mypy ab_hub
pytest
```

## Licença

MIT (a confirmar)

---

**AB-hub — Sabe o que construiu. Controla o que possui.**
