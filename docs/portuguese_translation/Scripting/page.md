# Scripting (Lua)

Visão geral
- O GSCX possui um mecanismo de scripting opcional em Lua (LuaJIT via o pacote "lupa"). Use para automatizar tarefas como carregar módulos, preparar pendrive virtual ou rodar operações em lote no carregador do emulador.

Requisitos
- Dependência Python: lupa (bindings do LuaJIT)
- Instalação: pip install lupa

Onde usar
- GUI: aba Scripting dentro do aplicativo
- CLI: gscx_app --script caminho/para/script.lua [--bundle arquivo.gscb | --load-default] [--boot-recovery]

Início rápido (GUI)
1) Abra a aba Scripting
2) Escreva um script Lua ou clique em Carregar Script para abrir um .lua
3) Clique em Executar para rodar tudo, Executar Seleção para apenas as linhas destacadas, ou Executar Arquivo para rodar um arquivo diretamente
4) Use Limpar Saída para limpar o console de saída

Início rápido (CLI)
- Carregar módulos padrão e rodar um script:
  gscx_app --load-default --script meu_script.lua
- Carregar um bundle e rodar um script, depois iniciar recovery:
  gscx_app --bundle GSCore.gscb --script setup.lua --boot-recovery

API Lua (tabela: gscx)
- print(...): Imprime na saída do scripting
- log(msg): Envia log para o canal principal
- sleep(segundos): Pausa a execução por segundos
- check_cancel(): Lança erro se o usuário solicitou cancelamento
- load_modules(): Carrega DLLs padrão
- load_bundle(path): Carrega bundle GSCore (.gscb)
- boot_recovery(): Executa GSCX_RecoveryEntry após carregar módulos
- setenv(chave, valor): Define variável de ambiente
- getenv(chave): Lê variável de ambiente
- cwd(): Obtém diretório atual
- chdir(path): Muda diretório atual
- exists(path): Verifica existência
- join(a, b, ...): Concatena caminhos
- abspath(path): Caminho absoluto
- dirname(path): Diretório pai
- basename(path): Nome do arquivo
- listdir([path]): Lista conteúdos
- read_text(path[, encoding]): Lê arquivo texto
- write_text(path, content[, encoding]): Escreve arquivo texto
- mkdir(path[, exist_ok]): Cria diretório (recursivo)

Exemplos
Carregar módulos padrão e iniciar recovery:

-- exemplo1.lua
print('GSCX scripting: recovery')
gscx.load_modules()
gscx.boot_recovery()

Preparar estrutura de pendrive virtual em uma pasta:

-- exemplo2.lua
local root = gscx.abspath('C:/GSCX/pendrive')
gscx.mkdir(root)
local pup = 'C:/firmwares/PS3UPDAT.PUP'
if not gscx.exists(pup) then
  error('PUP não encontrado: '..pup)
end
-- copiar PUP como PS3UPDAT.PUP (para binário use io.open('rb'/'wb'))
local dest = gscx.join(root, 'PS3UPDAT.PUP')
local content = gscx.read_text(pup, 'latin1')
local f = io.open(dest, 'wb'); f:write(content); f:close()
print('Preparado em '..root)

Dicas
- O engine alterna o diretório de trabalho para a pasta do script quando rodando via run_file(), facilitando caminhos relativos
- Use gscx.check_cancel() periodicamente em laços longos para que Parar responda rapidamente
- Para operações binárias, use io.open do Lua em modo 'rb'/'wb'

Solução de problemas
- Se aparecer "Lua runtime não disponível", instale o lupa: pip install lupa
- No Windows com Python 3.12+, use as wheels do PyPI; se falhar, considere Python 3.10/3.11

Créditos
- LuaJIT via lupa
- PySide6 para a GUI