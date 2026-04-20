# Cinderleaf (PT-BR)

Este documento é a versão em Português (Brasil) do README público do Cinderleaf.

- Traduzido da base em inglês no commit: `e06092c`
- Status da tradução: `completo (linha 1.5.0)`
- Documento-fonte (EN): [README raiz](../../../README.md)

**Cinderleaf** é um gerenciador de mods para desktop de **Stardew Valley**, com releases portáteis para Windows e Linux.

`for Stardew Valley` é uma descrição, não afiliação oficial. Cinderleaf é uma ferramenta da comunidade e não é endossada pelo ConcernedApe.

Versão atual do projeto: **1.5.0**

Última versão pública empacotada: **1.5.0**

Se você quiser o passo a passo completo, leia o [Guia do Usuário (PT-BR)](USER_GUIDE.md).

## O que o Cinderleaf faz bem

- organiza pastas de mods
- detecta arquivos de mod baixados em um só lugar
- mantém revisão antes de escrever arquivos
- mostra dependências obrigatórias faltando durante o planejamento
- permite perfis diferentes para saves/playstyles diferentes
- oferece sandbox para testes mais seguros
- facilita recuperação e rollback

A ideia é deixar o fluxo do dia a dia mais calmo e claro, sem te prender em processos longos.

## Partes principais do app

- `Library`: lista de mods, updates, launch, perfis e ações relacionadas
- `SMAPI`: helpers de versão/log/troubleshooting
- `Packages`: entrada de arquivos por watcher ou `Add package`
- `Install`: revisão final antes de escrever no disco
- `Discover`: busca read-only de páginas/fontes
- `Compare`: comparação read-only entre real e sandbox
- `History`: cópias arquivadas e histórico de instalação
- `Setup`: pastas, backup, restore/import e configurações extras

## Por que a versão `1.5.0` importa

- UI mais calma e consistente nos workspaces principais
- `Archive` + `Recovery` consolidados em `History`
- fluxo de `Packages` mais rápido (`Add package`, handoff melhor, abertura automática de `Install` quando o próximo passo é óbvio)
- dependências mais visíveis no fluxo normal
- mais cobertura de localização PT-BR no app
- lane Linux portátil experimental disponível

Histórico completo: [CHANGELOG.md](../../../CHANGELOG.md)

## Download da versão portátil

Os artefatos públicos são publicados no GitHub Releases.

1. Abra [Releases](https://github.com/meiameiameia/Cinderleaf/releases).
2. Baixe o artefato da sua plataforma.
3. Extraia para uma pasta comum.
4. Execute `Cinderleaf.exe` (Windows) ou `./Cinderleaf` (Linux).

Se houver arquivos de checksum, valide SHA256 antes de usar.

## Limites atuais

- downloads ainda são manuais
- `Compare` continua read-only
- instalação continua explícita e revisada (sem install silencioso)
- restore de saves continua manual
- Windows é a plataforma principal hoje
- Linux portátil está disponível, mas ainda em fase experimental

## Idiomas da documentação

- English:
  - [README](../../../README.md)
  - [User Guide](../../USER_GUIDE.md)
- Português (Brasil):
  - [README (PT-BR)](README.md)
  - [Guia do Usuário (PT-BR)](USER_GUIDE.md)

## Ajuda e links

- Guia completo (EN): [docs/USER_GUIDE.md](../../USER_GUIDE.md)
- Projeto no GitHub: [Cinderleaf](https://github.com/meiameiameia/Cinderleaf)
- Releases oficiais: [GitHub Releases](https://github.com/meiameiameia/Cinderleaf/releases)
