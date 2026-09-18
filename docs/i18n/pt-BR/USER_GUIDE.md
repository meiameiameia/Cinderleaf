# Guia do Usuário Cinderleaf (PT-BR)

Este é o guia em Português (Brasil) da linha de trabalho `1.6.0` em source.

A última versão pública empacotada ainda é a `1.5.0`.

- Traduzido da base em inglês no commit: `a1074f1`
- Status da tradução: `completo (linha 1.6.0)`
- Documento-fonte (EN): [docs/USER_GUIDE.md](../../USER_GUIDE.md)

Se você quiser uma visão rápida antes, veja o [README (PT-BR)](README.md).

## 1. Para que serve o Cinderleaf

Cinderleaf ajuda quem quer organizar mods de Stardew Valley sem transformar tudo em uma tarefa pesada.

Ele ajuda você a:

- ver o que está instalado
- centralizar arquivos de mod baixados
- revisar instalação antes de mudar arquivos
- detectar dependências obrigatórias faltando no planejamento
- manter perfis diferentes por save/playstyle
- usar sandbox para testar com mais segurança
- recuperar ou desfazer alterações com mais confiança

Você não precisa usar todos os recursos para tirar valor do app.

## 2. Configuração inicial mais simples

Comece por `Configuração`.

Pastas principais:

- pasta do jogo
- pasta `Mods` real
- pasta `Mods` sandbox

A sandbox é opcional, mas recomendada para testes.

## 3. Fluxo normal do dia a dia

Pense assim:

1. trazer arquivos para `Pacotes`
2. revisar em `Instalar`
3. usar `Biblioteca` para gerenciar, atualizar e lançar

## 4. Pacotes

`Pacotes` é a entrada de arquivos.

Você pode:

- clicar `Adicionar pacote` para um arquivo específico
- usar watcher para monitorar uma ou duas pastas de download

Fluxo típico:

1. Abra `Pacotes`.
2. Use `Adicionar pacote` ou inicie watcher.
3. Deixe o app detectar os arquivos.
4. Marque as linhas que quer processar.
5. Defina o alvo de comparação.
6. Clique `Abrir Instalar`.

Importante:

- `Pacotes` não instala sozinho
- é etapa de revisão
- o app pode abrir `Instalar` automaticamente quando houver um único pacote óbvio, mas ainda para na revisão

## 5. Instalar

`Instalar` é o checkpoint final antes de escrever arquivos.

Nele você:

- confirma destino
- revisa substituições
- vê avisos de dependência
- lê o resumo
- aplica só quando estiver certo

## 6. Biblioteca

`Biblioteca` é a tela principal para uso diário.

Use para:

- escanear mods instalados
- checar atualizações
- abrir páginas de origem
- iniciar o jogo
- iniciar com SMAPI
- iniciar teste em sandbox
- gerenciar perfis

### Como atualizar um mod

1. Em `Biblioteca`, clique `Verificar atualizações`.
2. Selecione uma linha com `Atualização disponível`.
3. Clique `Abrir página` (ou `Encontrar origem`) e baixe o novo arquivo.
4. Vá para `Pacotes` e deixe watcher detectar, ou use `Adicionar pacote`.
5. Selecione a linha, escolha alvo de comparação e clique `Abrir Instalar`.
6. Revise avisos, substituições e dependências, depois aplique.

Fluxo seguro: detectar -> fila -> revisar -> escrever.

## 7. SMAPI

Use `SMAPI` para:

- checar versão da SMAPI
- abrir o log mais recente
- abrir o site da SMAPI
- troubleshooting de launch modded

## 8. Perfis

Perfis permitem manter conjuntos diferentes de mods sem mover pastas manualmente.

- `Padrão` espelha a biblioteca principal
- perfis customizados permitem seleções menores ou diferentes

Com dependências:

- ao habilitar mod em perfil customizado, dependência já instalada pode ser auto-adicionada com segurança
- se não estiver instalada, o app avisa

## 9. Sandbox

Sandbox é uma configuração separada de `Mods`.

- seu `Mods` real fica preservado
- sandbox vira área de teste

Se der certo, você promove depois. Se der errado, o impacto fica isolado.

## 10. Comparar

Executar `Comparar` é uma ação somente leitura. Ela mostra as diferenças entre real e sandbox sem mudar nenhum dos lados:

- só no real
- só no sandbox
- versões diferentes

Depois de selecionar uma diferença, você escolhe uma direção explícita:

- `Sincronizar real -> sandbox` quando a cópia ao vivo deve substituir o lado de teste
- `Sincronizar sandbox -> real` quando a cópia testada deve substituir o lado ao vivo

Antes de escrever, o Cinderleaf mostra uma revisão específica para a direção escolhida, com origem, destino, novas entradas, substituições e local do arquivo. Cópias substituídas no destino são arquivadas, e a operação fica registrada no histórico de recuperação. Famílias de mod com várias pastas vinculadas são tratadas como uma única seleção lógica.

Nada é sincronizado automaticamente. Cancelar a revisão deixa os dois lados intactos.

## 11. Histórico

`Histórico` concentra estado antigo e rollback.

Abas:

- `Cópias arquivadas`
- `Histórico de instalação`

### Cópias arquivadas

- navegar cópias arquivadas
- restaurar cópia
- excluir cópia
- limpar cópias antigas

### Histórico de instalação

- inspecionar histórico de instalação
- revisar rollback
- aplicar recuperação após revisão

### Se uma instalação falhar

A revisão vale para o pacote e o destino verificados. Se o pacote, os arquivos de
destino ou os manifests dos mods instalados mudarem, crie e revise um novo plano.
Sandbox e Mods reais precisam ser pastas separadas; uma não pode conter a outra.
Pastas vinculadas (incluindo junctions do Windows) não são suportadas na instalação
de pacotes compactados.

- **Falhou — alterações desfeitas:** o lote falhou e suas alterações nos mods foram
  desfeitas. Resolva o problema informado e crie um novo plano.
- **Não finalizada** ou **Incompleta:** não tente novamente nem exclua pastas de
  preparação ou arquivos de recuperação. Abra a operação no Histórico e preserve o
  registro de recuperação indicado nos detalhes. Essas operações precisam de inspeção;
  a recuperação automática fica desabilitada quando o resultado é incerto. Peça ajuda
  antes de mover arquivos e confira se há caminhos pessoais no registro antes de compartilhá-lo.
- **Concluída:** a instalação e seu registro final foram concluídos. A recuperação
  normal, com revisão, continua disponível quando as verificações de segurança passam.

Falhas comuns desfazem o lote. Uma interrupção do aplicativo, bloqueio de arquivos
durante a recuperação ou falha ao salvar o registro final pode exigir recuperação
manual. Não há garantia de recuperação automática após falta de energia.

A recuperação de uma instalação concluída na versão 1.6.0 usa selos de conteúdo. O
Cinderleaf confirma que a pasta instalada e, em uma substituição, a cópia original
arquivada ainda correspondem à operação revisada. Se qualquer uma mudou, a
recuperação automática é bloqueada para preservar alterações mais novas. Registros
antigos sem esses selos continuam visíveis, mas não permitem recuperação automática.

Uma recuperação concluída não exclui definitivamente o mod atual. Primeiro ela move
a pasta atual para o arquivo da operação e, quando necessário, restaura a cópia
anterior. O Histórico mostra o caminho retido e o registro da recuperação. Se um lote
de recuperação falhar, o Cinderleaf tenta desfazer o lote inteiro; preserve todos os
caminhos mostrados no Histórico quando o resultado for `Incompleta`.

Somente uma janela do Cinderleaf pode ficar aberta por vez. Uma segunda cópia para
antes de carregar o workspace, evitando alterações simultâneas nas mesmas pastas de
Mods e no histórico.

**Compatibilidade do Histórico:** a versão 1.6.0 lê o histórico existente, mas grava
um formato novo. Versões anteriores, incluindo a 1.5.0, não conseguem lê-lo. Antes de
testar a 1.6.0, guarde um backup do estado do gerenciador. Não use uma versão antiga
com o estado atualizado nem restaure estado antigo sobre uma biblioteca de mods
alterada sem revisar a recuperação.

## 12. Backup e restore

Exportação de backup pode incluir:

- estado do gerenciador e perfis
- mods gerenciados e snapshots de config
- arquivos de archive
- saves de Stardew (opcional)

Restore/import já cobre o lado guiado de mod, config e perfil.

Saves continuam com restore manual.

## 13. Descobrir

`Descobrir` ajuda a buscar mods por nome, autor ou UniqueID e abrir páginas.

Não instala por conta própria.

## 14. Se algo der errado

Ao reportar bug, inclua:

- versão do Cinderleaf
- SO e versão (ex.: Windows 11, Ubuntu 24.04)
- workspace usado
- status ou erro observado
- se ocorre só no pacote portátil ou também em source

Para SMAPI, diga também se ocorreu em:

- `Mods` real
- `Mods` sandbox
- perfil específico

## 15. Bons hábitos

- use `Adicionar pacote` para fluxo rápido de 1 arquivo
- use watcher quando baixar vários arquivos
- trate `Instalar` como checkpoint final antes de escrita
- prefira perfis em vez de mover pasta manualmente
- use sandbox para experimento seguro
- use `Histórico` para restore ou rollback

## 16. Limites atuais

- downloads continuam manuais
- a sincronização em `Comparar` continua explícita e baseada na seleção; ela não espelha pastas inteiras silenciosamente
- o app acelera revisão, mas não instala silenciosamente
- restore de save continua manual
- Windows segue como plataforma principal
- Linux portátil está disponível, porém experimental
