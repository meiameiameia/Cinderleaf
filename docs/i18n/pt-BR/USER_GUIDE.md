# Guia do Usuário Cinderleaf (PT-BR)

Este é o guia em Português (Brasil) da linha de release `1.5.0`.

- Traduzido da base em inglês no commit: `e06092c`
- Status da tradução: `completo (linha 1.5.0)`
- Documento-fonte (EN): [docs/USER_GUIDE.md](../../USER_GUIDE.md)

Se você quiser uma visão rápida antes, veja o [README (PT-BR)](README.md).

## 1. Para que serve o Cinderleaf

Cinderleaf ajuda quem quer organizar mods de Stardew Valley sem transformar tudo em uma tarefa pesada.

Ele te ajuda a:

- ver o que está instalado
- centralizar arquivos de mod baixados
- revisar instalação antes de mudar arquivos
- detectar dependências obrigatórias faltando durante o planejamento
- manter perfis diferentes por save/playstyle
- usar sandbox para testar com mais segurança
- recuperar/voltar alterações com mais confiança

Você não precisa usar todos os recursos para tirar valor do app.

## 2. Setup inicial mais simples

Comece por `Setup`.

Pastas principais:

- pasta do jogo
- pasta `Mods` real
- pasta `Mods` sandbox

A sandbox é opcional, mas recomendada para testes.

## 3. Fluxo normal do dia a dia

Pense assim:

1. trazer arquivos para `Packages`
2. revisar em `Install`
3. usar `Library` para gerenciar/atualizar/lançar

## 4. Packages

`Packages` é a entrada de arquivos.

Você pode:

- clicar `Add package` para um arquivo específico
- usar watcher para monitorar uma ou duas pastas de download

Fluxo típico:

1. Abra `Packages`.
2. Use `Add package` ou inicie watcher.
3. Deixe o app detectar os arquivos.
4. Marque as linhas que quer processar.
5. Defina o alvo de comparação.
6. Abra `Install`.

Importante:

- `Packages` não instala sozinho
- é etapa de revisão
- o app pode abrir `Install` automaticamente quando houver um único pacote óbvio, mas ainda para na revisão

## 5. Install

`Install` é o checkpoint final antes de escrever arquivos.

Nele você:

- confirma destino
- revisa substituições
- vê avisos de dependência
- lê o resumo
- aplica só quando estiver certo

## 6. Library

`Library` é a tela principal para uso diário.

Use para:

- escanear mods instalados
- checar updates
- abrir páginas de origem
- iniciar jogo
- iniciar com SMAPI
- iniciar teste em sandbox
- gerenciar perfis

### Como atualizar um mod

1. Em `Library`, clique `Check updates`.
2. Selecione linha com `Update available`.
3. Clique `Open page` (ou `Find source`) e baixe o novo arquivo.
4. Vá para `Packages` e deixe watcher detectar, ou use `Add package`.
5. Selecione a linha, escolha alvo de comparação e abra `Install`.
6. Revise warnings/substituições/dependências e aplique.

Fluxo seguro: detectar -> fila -> revisar -> escrever.

## 7. SMAPI

Use `SMAPI` para:

- checar versão da SMAPI
- abrir o log mais recente
- abrir site da SMAPI
- troubleshooting de launch modded

## 8. Perfis

Perfis permitem manter conjuntos diferentes de mods sem mover pastas manualmente.

- `Default` espelha a biblioteca principal
- perfis customizados permitem seleções menores ou diferentes

Com dependências:

- ao habilitar mod em perfil customizado, dependência já instalada pode ser auto-adicionada com segurança
- se não estiver instalada, o app avisa

## 9. Sandbox

Sandbox é uma configuração separada de `Mods`.

- seu `Mods` real fica preservado
- sandbox vira área de teste

Se der certo, você promove depois. Se der errado, o impacto fica isolado.

## 10. Compare

`Compare` é read-only.

Serve para revisar diferença entre real e sandbox:

- só no real
- só no sandbox
- versões diferentes

## 11. History

`History` concentra estado antigo e rollback.

Abas:

- `Archived copies`
- `Install history`

### Archived copies

- navegar cópias arquivadas
- restaurar cópia
- deletar cópia
- limpar cópias antigas

### Install history

- inspecionar histórico de install
- revisar rollback
- aplicar recovery após revisão

## 12. Backup e restore

Exportação de backup pode incluir:

- estado do manager e perfis
- mods gerenciados e snapshots de config
- arquivos de archive
- saves de Stardew (opcional)

Restore/import já cobre o lado guiado de mod/config/perfil.

Saves continuam com restore manual.

## 13. Discover

`Discover` ajuda a buscar mods por nome, autor ou UniqueID e abrir páginas.

Não instala por conta própria.

## 14. Se algo der errado

Ao reportar bug, inclua:

- versão do Cinderleaf
- SO e versão (ex.: Windows 11, Ubuntu 24.04)
- workspace usado
- status/erro observado
- se ocorre só no pacote portátil ou também em source

Para SMAPI, diga também se ocorreu em:

- `Mods` real
- `Mods` sandbox
- perfil específico

## 15. Bons hábitos

- use `Add package` para fluxo rápido de 1 arquivo
- use watcher quando baixar vários arquivos
- trate `Install` como checkpoint final antes de escrita
- prefira perfis em vez de mover pasta manualmente
- use sandbox para experimento seguro
- use `History` para restore/rollback

## 16. Limites atuais

- downloads continuam manuais
- `Compare` continua read-only
- app acelera revisão, mas não instala silenciosamente
- restore de save continua manual
- Windows segue como plataforma principal
- Linux portátil está disponível, porém experimental
