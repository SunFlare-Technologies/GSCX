# GSCX Setup and Installation Guide

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10 (64-bit) or later
- **Processor**: Intel Core i5-4590 / AMD FX 8350 or equivalent
- **Memory**: 4 GB RAM
- **Graphics**: DirectX 11 compatible GPU
- **Storage**: 2 GB available space
- **Network**: Internet connection for initial setup

### Recommended Requirements
- **Operating System**: Windows 11 (64-bit)
- **Processor**: Intel Core i7-8700K / AMD Ryzen 5 3600 or better
- **Memory**: 8 GB RAM or more
- **Graphics**: NVIDIA GTX 1060 / AMD RX 580 or better
- **Storage**: 10 GB available space (SSD recommended)
- **Network**: Broadband internet connection

## Prerequisites Installation

### Development Tools

#### Option 1: Visual Studio (Recommended)
1. Download **Visual Studio 2022 Community** from Microsoft
2. During installation, select:
   - **Desktop development with C++** workload
   - **Windows 10/11 SDK** (latest version)
   - **CMake tools for C++**
   - **Git for Windows**

#### Option 2: MinGW-w64
1. Install **MSYS2** from https://www.msys2.org/
2. Open MSYS2 terminal and run:
   ```bash
   pacman -S mingw-w64-x86_64-gcc
   pacman -S mingw-w64-x86_64-cmake
   pacman -S mingw-w64-x86_64-ninja
   pacman -S git
   ```

### Python Environment
1. Install **Python 3.10** or **3.11** from python.org
2. Ensure Python is added to system PATH
3. Verify installation:
   ```powershell
   python --version
   pip --version
   ```

### .NET Runtime
1. Install **.NET 6.0 Runtime** from Microsoft
2. Install **.NET 6.0 SDK** for development
3. Verify installation:
   ```powershell
   dotnet --version
   ```

## Project Setup

### 1. Clone Repository
```powershell
# Clone the main repository
git clone https://github.com/your-org/gscx.git
cd gscx

# Initialize submodules (if any)
git submodule update --init --recursive
```

### 2. Python Environment Setup
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install Python dependencies
cd pyapp
pip install -r requirements.txt
```

### 3. Build C++ Components

#### Using Visual Studio
```powershell
# Run automated build script
.\build_cpp.ps1

# Or build manually
cd src
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
```

#### Using MinGW
```powershell
# Set up MinGW environment
.\mingw_terminal.bat

# Build with MinGW
cd src
mkdir build
cd build
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build .
```

### 4. Build .NET Components
```powershell
# Build spoofing modules
.\build_dotnet.ps1

# Or build manually
cd dotnet\Spoofing
dotnet restore
dotnet build --configuration Release
```

### 5. Verify Installation
```powershell
# Test Python GUI
.\run_gui.ps1

# Test C++ components
cd src\build\Release
.\gscx_core_test.exe

# Test .NET components
cd dotnet\Spoofing\bin\Release\net6.0
dotnet Spoofing.dll --test
```

## Configuration

### Initial Configuration
1. Launch the GUI application:
   ```powershell
   .\run_gui.ps1
   ```

2. **First Run Setup**:
   - Select PS3 model (CECHA01, CECHB01, etc.)
   - Configure memory settings
   - Set up storage paths
   - Choose language preference

3. **Hardware Configuration**:
   - **CPU Emulation**: Set thread count (recommended: CPU cores - 1)
   - **Memory**: Configure XDR and GDDR3 allocation
   - **Storage**: Set paths for NAND, HDD, and temporary files

### Advanced Configuration

#### config.ini Settings
```ini
[System]
model=CECHA01
memory_xdr=256
memory_gddr3=256
cpu_threads=6

[Paths]
nand_path=./data/nand.bin
hdd_path=./data/hdd.img
temp_path=./temp

[Emulation]
boot_mode=normal
recovery_enabled=true
syscon_virtualized=true

[GUI]
language=en
theme=dark
log_level=info
```

#### Logging Configuration
```ini
[Logging]
level=INFO
file_output=true
console_output=true
max_file_size=10MB
max_files=5
```

## PS3 Firmware Setup

### Obtaining Firmware
1. **Legal Requirements**: You must own a PS3 console
2. **Firmware Extraction**: Use official Sony update files (PS3UPDAT.PUP)
3. **Supported Versions**: 4.88, 4.89, 4.90, 4.91

### Firmware Installation
1. Place firmware file in `./firmware/` directory
2. Rename to match expected format: `PS3UPDAT_4.88.PUP`
3. Launch GSCX and select "Install Firmware"
4. Follow installation wizard

### NAND/NOR Dump Setup
1. **Hardware Requirements**: Compatible flasher (E3 ODE Pro, etc.)
2. **Dump Process**: Follow hardware-specific instructions
3. **File Placement**: Copy dumps to `./data/` directory
4. **Verification**: Use built-in checksum validation

## Troubleshooting Installation

### Common Build Issues

#### CMake Configuration Errors
```powershell
# Clear CMake cache
Remove-Item -Recurse -Force src\build\CMakeCache.txt
Remove-Item -Recurse -Force src\build\CMakeFiles

# Regenerate build files
cd src\build
cmake .. -G "Visual Studio 17 2022" -A x64
```

#### Python Dependency Issues
```powershell
# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools wheel

# Reinstall PySide6
pip uninstall PySide6
pip install PySide6==6.5.2

# Clear pip cache
pip cache purge
```

#### .NET Build Failures
```powershell
# Clean .NET build artifacts
dotnet clean
Remove-Item -Recurse -Force dotnet\*\bin, dotnet\*\obj

# Restore packages
dotnet restore --force
dotnet build --no-restore
```

### Runtime Issues

#### GUI Won't Start
1. **Check Python Environment**:
   ```powershell
   python -c "import PySide6; print('PySide6 OK')"
   ```

2. **Verify Qt Installation**:
   ```powershell
   python -c "from PySide6.QtWidgets import QApplication; print('Qt OK')"
   ```

3. **Check Display Scaling**:
   ```powershell
   set QT_SCALE_FACTOR=1.0
   .\run_gui.ps1
   ```

#### C++ Module Loading Errors
1. **Check Dependencies**:
   ```powershell
   # Using Dependency Walker or similar tool
   depends.exe src\build\Release\gscx_core.dll
   ```

2. **Verify Runtime Libraries**:
   - Install Visual C++ Redistributable 2022
   - Ensure all DLLs are in PATH or application directory

#### Memory/Performance Issues
1. **Increase Virtual Memory**:
   - Set pagefile to 8-16GB
   - Ensure sufficient disk space

2. **Optimize CPU Affinity**:
   ```powershell
   # Set process affinity (example for 8-core CPU)
   $process = Get-Process gscx_gui
   $process.ProcessorAffinity = 0xFE  # Use cores 1-7
   ```

### Hardware Compatibility

#### GPU Issues
- **DirectX 11 Support**: Verify with `dxdiag`
- **Driver Updates**: Install latest GPU drivers
- **Hardware Acceleration**: Enable in Windows settings

#### CPU Compatibility
- **SSE4.2 Support**: Required for optimized code paths
- **AVX Support**: Recommended for performance
- **Virtualization**: Enable VT-x/AMD-V in BIOS

## Performance Optimization

### System Optimization
1. **Disable Windows Defender Real-time Protection** (temporarily)
2. **Set High Performance Power Plan**
3. **Close Unnecessary Background Applications**
4. **Increase Process Priority**:
   ```powershell
   Start-Process -FilePath ".\run_gui.ps1" -Verb RunAs -WindowStyle Normal
   ```

### Application Optimization
1. **Thread Configuration**:
   - Set CPU threads to (Physical Cores - 1)
   - Enable SMT/Hyperthreading if available

2. **Memory Settings**:
   - Allocate maximum available RAM
   - Use SSD for temporary files

3. **Graphics Settings**:
   - Enable hardware acceleration
   - Set appropriate resolution scaling

## Security Considerations

### Antivirus Configuration
- **Add Exclusions** for GSCX directory
- **Whitelist Executables**: `gscx_core.dll`, `gscx_gui.exe`
- **Disable Real-time Scanning** for development

### Firewall Settings
- **Allow Network Access** for update checking
- **Block Unnecessary Connections** for security

### File Permissions
- **Run as Administrator** if needed
- **Set Full Control** on GSCX directory
- **Verify Write Permissions** for log and temp directories

## Getting Help

### Documentation Resources
- **API Documentation**: `docs/API/`
- **Core System Docs**: `docs/Core/`
- **Bootloader Guide**: `docs/Bootloader/`
- **Scripting Reference**: `docs/Scripting/`

### Community Support
- **GitHub Issues**: Report bugs and feature requests
- **Discord Server**: Real-time community support
- **Wiki**: Community-maintained documentation
- **Forums**: Discussion and troubleshooting

### Professional Support
- **Commercial License**: Enterprise support available
- **Custom Development**: Consulting services
- **Training**: Developer workshops and courses

For additional help, see the [troubleshooting guide](troubleshooting.md) or contact the development team.