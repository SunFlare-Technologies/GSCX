# GSCX C++ Core Documentation

Esta documentação cobre os componentes C++ do GSCX, incluindo os módulos de recuperação e núcleo do emulador.

## Estrutura dos Módulos C++

### Core Module (`src/core/`)

O módulo core contém os componentes fundamentais do emulador:

#### Headers (`src/core/include/`)

- **`cell_ir.h`** - Definições para a representação intermediária do processador Cell
- **`gscore_format.h`** - Formato de dados do núcleo gráfico
- **`host_services_c.h`** - Interface C para serviços do sistema host
- **`logger.h`** - Sistema de logging do emulador
- **`module_api.h`** - API para módulos do emulador

#### Implementações (`src/core/src/`)

- **`decoder.cpp`** - Decodificador de instruções do PS3
  - Responsável por decodificar instruções PowerPC e SPU
  - Converte instruções nativas em representação intermediária

- **`gscore_loader.cpp`** - Carregador do núcleo gráfico
  - Gerencia o carregamento de shaders e recursos gráficos
  - Interface com o RSX (Reality Synthesizer)

- **`jit_runtime.cpp`** - Runtime do compilador Just-In-Time
  - Compila código PowerPC para código nativo x86-64
  - Otimizações de performance em tempo de execução

- **`module_host.cpp`** - Host de módulos do sistema
  - Gerencia carregamento e execução de módulos PRX
  - Interface com o sistema de arquivos virtual

- **`translator.cpp`** - Tradutor de instruções
  - Traduz instruções Cell BE para arquitetura host
  - Implementa otimizações de bloco básico

### Recovery Module (`src/modules/recovery/`)

O módulo recovery implementa funcionalidades de recuperação e boot do sistema:

#### Headers

- **`ee_engine.h`** - Engine de emulação do Emotion Engine (compatibilidade PS2)
- **`ps3_models.h`** - Definições de modelos de PS3 suportados
- **`pup_reader.h`** - Leitor de arquivos PUP (PlayStation Update Package)
- **`recovery_i18n.h`** - Internacionalização do modo recovery
- **`recovery_mode.h`** - Interface do modo de recuperação

#### Implementações

- **`bootloader.cpp`** - Bootloader do sistema
  - Inicialização do hardware virtual
  - Carregamento do firmware

- **`ee_engine.cpp`** - Implementação do Emotion Engine
  - Emulação de compatibilidade com PS2
  - Processamento de instruções MIPS

- **`ps3_models.cpp`** - Suporte a modelos de PS3
  - Detecção automática de modelo
  - Configurações específicas por hardware

- **`pup_reader.cpp`** - Leitor de PUP
  - Extração de firmware do PS3
  - Validação de integridade de arquivos

- **`recovery.cpp`** - Modo de recuperação principal
  - Interface de recuperação do sistema
  - Diagnósticos de hardware

- **`recovery_entry.c`** - Ponto de entrada do recovery (C)
  - Inicialização de baixo nível
  - Interface com assembly

- **`recovery_entry.asm`** - Código assembly de entrada
  - Inicialização de registradores
  - Setup de stack

- **`recovery_i18n.cpp`** - Sistema de internacionalização
  - Suporte a múltiplos idiomas
  - Carregamento de strings localizadas

- **`recovery_mode.cpp`** - Implementação do modo recovery
  - Menu de opções de recuperação
  - Ferramentas de diagnóstico

## Arquitetura Técnica

### Fluxo de Emulação

1. **Inicialização** (`bootloader.cpp`)
2. **Decodificação** (`decoder.cpp`)
3. **Tradução** (`translator.cpp`)
4. **Execução JIT** (`jit_runtime.cpp`)
5. **Renderização** (`gscore_loader.cpp`)

### Compatibilidade

- **PowerPC 970** - Processador principal do Cell BE
- **SPU** - Synergistic Processing Units
- **RSX** - Reality Synthesizer (GPU)
- **PS2 EE** - Emotion Engine (retrocompatibilidade)

### Build System

Cada módulo possui seu próprio `CMakeLists.txt` para compilação independente:

```cmake
# Exemplo de configuração
set(CMAKE_CXX_STANDARD 17)
find_package(LLVM REQUIRED)
target_link_libraries(gscx_core ${LLVM_LIBRARIES})
```

## Dependências

- **LLVM** - Para compilação JIT
- **OpenGL/Vulkan** - Renderização gráfica
- **SDL2** - Interface de sistema
- **zlib** - Compressão de dados

## Notas de Desenvolvimento

- Código otimizado para performance em tempo real
- Suporte a debugging com GDB
- Testes unitários em `tests/cpp/`
- Documentação Doxygen em headers

---

*Documentação gerada para GSCX v0.4.1 alpha*