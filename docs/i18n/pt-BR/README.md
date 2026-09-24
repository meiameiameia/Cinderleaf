# Cinderleaf (PT-BR)

Este documento é a versão em Português (Brasil) do README público do Cinderleaf.

- Status da tradução: `completo (versão 1.6.0)`
- Documento-fonte (EN): [README raiz](../../../README.md)

**Cinderleaf** é um gerenciador de mods para desktop de **Stardew Valley**. A versão portátil atual é para Windows; também existe uma versão experimental anterior para Linux.

`for Stardew Valley` é uma descrição, não uma afiliação oficial. Cinderleaf é uma ferramenta da comunidade e não é endossada por ConcernedApe.

Versão atual do projeto: **1.6.0**

Última versão pública empacotada: **1.6.0**

Se você quiser o passo a passo completo, leia o [Guia do Usuário (PT-BR)](USER_GUIDE.md).

## O que o Cinderleaf faz bem

- organiza suas pastas de mods
- detecta arquivos de mod baixados em um só lugar
- mantém revisão antes de escrever arquivos
- detecta dependências obrigatórias faltando no planejamento
- permite perfis diferentes para saves/playstyles diferentes
- oferece sandbox para testes mais seguros
- facilita recuperação e rollback

A ideia é deixar o fluxo do dia a dia mais calmo e claro, sem te prender em processos longos.

## Partes principais do app

- `Biblioteca`: lista de mods, verificações de atualização, launch, perfis e ações relacionadas
- `SMAPI`: helpers de versão, log e troubleshooting
- `Pacotes`: entrada de arquivos por watcher ou `Adicionar pacote`
- `Instalar`: revisão final antes de escrever no disco
- `Descobrir`: busca somente leitura de páginas e fontes
- `Comparar`: revisão das diferenças e sincronização explícita `real -> sandbox` ou `sandbox -> real` depois de confirmar o lado que deve vencer
- `Histórico`: cópias arquivadas e histórico de instalação
- `Configuração`: pastas, backup, restore/import e configurações extras

## Novidades da versão `1.6.0`

- `Comparar` permite sincronizar mods selecionados entre as pastas reais e sandbox nos dois sentidos, sempre com uma revisão antes da gravação.
- Pastas relacionadas ao mesmo mod continuam juntas durante a sincronização.
- Planos de instalação recusam arquivos ou destinos alterados; a recuperação verifica se uma instalação concluída ainda corresponde ao registro.
- Melhorias na identificação de fontes de atualização, no resumo do log do SMAPI, na interface e no texto em português e inglês.
- Novo ícone do Cinderleaf e identidade atualizada no pacote portátil para Windows.

Antes de atualizar, guarde um backup do estado do Cinderleaf e das pastas de Mods. A versão `1.6.0` lê o histórico antigo, mas grava um formato que a `1.5.0` não consegue ler.

Histórico completo: [CHANGELOG.md](../../../CHANGELOG.md)

## Download da versão portátil

Os artefatos públicos são publicados no GitHub Releases.

1. Abra [Releases](https://github.com/meiameiameia/Cinderleaf/releases).
2. Baixe `cinderleaf-1.6.0-windows-portable.zip` para Windows. A versão experimental para Linux continua disponível no release `1.5.0`.
3. Extraia para uma pasta comum.
4. Execute `Cinderleaf.exe` (Windows) ou `./Cinderleaf` (Linux).

Confira o SHA-256 usando o arquivo de checksum publicado antes de usar.

O Cinderleaf permite apenas uma cópia em execução por vez, evitando que duas janelas
alterem simultaneamente as mesmas pastas de Mods ou o histórico de recuperação.

## Limites atuais

- downloads ainda são manuais
- a sincronização em `Comparar` é deliberada e baseada na seleção; ela nunca espelha pastas inteiras silenciosamente
- instalação continua explícita e revisada (sem install silencioso)
- restore de saves continua manual
- Windows é a plataforma principal hoje
- Linux portátil está disponível apenas na versão anterior `1.5.0` e ainda é experimental

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
