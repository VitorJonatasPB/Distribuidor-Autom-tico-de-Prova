# Distribuidor Automático de Provas

O **Distribuidor Automático de Provas** é uma solução de automação robótica (RPA) desenvolvida em Python para otimizar o processo de disponibilização de materiais e provas na plataforma de cursos do IBAD. O software integra uma interface gráfica (GUI) moderna com uma lógica de processamento de dados flexível, eliminando o trabalho manual de seleção individual de alunos.

## 🎯 Objetivo

Automatizar a distribuição de créditos e materiais para listas de alunos extraídas de planilhas locais ou remotas, garantindo precisão e gerando relatórios detalhados de execução.

## 🚀 Funcionalidades Principais

- **Ingestão de Dados Híbrida**:
  - Suporte a arquivos locais (`.csv`, `.xlsx`, `.xls`).
  - Integração direta com **Google Sheets** via conversão dinâmica de URL (Link de exportação CSV).
- **Filtragem Inteligente**: Aplica filtros baseados em colunas específicas da planilha (ex: filtrar apenas alunos que marcaram "✅" em determinada prova).
- **Automação Web Robusta (Selenium)**:
  - Gestão de perfis de usuário para persistência de login.
  - Lógica de _Retry_ (tentativa de redundância) para lidar com erros de _Stale Element_ ou latência de rede.
  - Busca inteligente no componente Select2 da plataforma.
- **Relatório de Auditoria**: Gera automaticamente um arquivo `relatorio_final.csv` com o status (Sucesso, Não Encontrado ou Erro) de cada aluno processado.
- **Interface Moderna**: Desenvolvida com `CustomTkinter`, oferecendo modo escuro e feedback de logs em tempo real.

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3.12+
- **Interface**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **Automação**: [Selenium WebDriver](https://www.selenium.dev/)
- **Manipulação de Dados**: [Pandas](https://pandas.pydata.org/)
- **Gerenciamento de Dependências**: [Poetry](https://python-poetry.org/)

## ⚙️ Configuração e Instalação

### Pré-requisitos

- Google Chrome instalado.
- Poetry instalado (`pip install poetry`).

### Instalação

1.  Clone o repositório:
    ```bash
    git clone https://github.com/seu-usuario/disponibilizar-prova.git
    ```
2.  Instale as dependências:
    ```bash
    poetry install
    ```
3.  Configure o arquivo `.env` (use o `.env.example` como base):
    ```env
    DISCIPLINA_NOME=NOME_DA_DISCIPLINA
    COLUNA_ALUNO=NOME
    ```

## 📋 Como Usar

1.  **Login**: Execute o programa e utilize o botão "Abrir Navegador" para realizar o login manual e resolver CAPTCHAs, se necessário.
2.  **Configuração de Dados**:
    - Selecione a origem (Computador ou Web).
    - Defina a **Coluna Filtro** e o **Valor Filtro** (Ex: Coluna `L10` e Valor `✅`).
3.  **Execução**: Clique em **INICIAR** e acompanhe os logs em tempo real. O robô irá filtrar os alunos, acessar a página de distribuição e selecionar cada um conforme a disciplina configurada.
4.  **Resultado**: Ao final, consulte o `relatorio_final.csv` para validar quem foi processado com sucesso.

---

_Desenvolvido por [Vitor Jonatas Paiva Barbosa](https://github.com/VitorJonatasPB)_
