param(
    [string]$BuildType = "RelWithDebInfo"
)

# Function to ensure required tooling is available
function Ensure-Tooling {
    Write-Host "Checking for required build tools..." -ForegroundColor Yellow
    
    # Check for MinGW first (preferred for cross-platform compatibility)
    $mingwFound = $false
    try {
        $gccVersion = & gcc --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Found MinGW GCC: $($gccVersion[0])" -ForegroundColor Green
            $mingwFound = $true
        }
    } catch {}
    
    # Check for MSVC if MinGW not found
    $msvcFound = $false
    if (-not $mingwFound) {
        try {
            $clPath = & where cl 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Found MSVC compiler at: $clPath" -ForegroundColor Green
                $msvcFound = $true
            }
        } catch {}
    }
    
    if (-not $mingwFound -and -not $msvcFound) {
        Write-Host "No C++ compiler found!" -ForegroundColor Red
        Write-Host "Please install one of the following:" -ForegroundColor Yellow
        Write-Host "  1. MinGW-w64 (recommended): https://www.mingw-w64.org/downloads/" -ForegroundColor Cyan
        Write-Host "  2. Visual Studio Build Tools (C++): https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022" -ForegroundColor Cyan
        throw "No C++ compiler available"
    }
    
    # Activate virtual environment if it exists
    if (Test-Path "venv\Scripts\Activate.ps1") {
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        & .\venv\Scripts\Activate.ps1
    }
    
    # Check and install CMake if needed
    try {
        $cmakeVersion = & cmake --version 2>$null
        if ($LASTEXITCODE -ne 0) { throw }
        Write-Host "Found CMake: $($cmakeVersion[0])" -ForegroundColor Green
    } catch {
        Write-Host "CMake not found, installing via pip..." -ForegroundColor Yellow
        & python -m pip install cmake
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install CMake via pip"
        }
        # Update PATH for current session
        $env:PATH = "$env:PATH;$((Get-Location).Path)\venv\Scripts"
    }
    
    # Check and install Ninja if needed (only if MinGW is available)
    if ($mingwFound) {
        try {
            $ninjaVersion = & ninja --version 2>$null
            if ($LASTEXITCODE -ne 0) { throw }
            Write-Host "Found Ninja: $ninjaVersion" -ForegroundColor Green
        } catch {
            Write-Host "Ninja not found, installing via pip..." -ForegroundColor Yellow
            & python -m pip install ninja
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to install Ninja via pip"
            }
            # Update PATH for current session
            $env:PATH = "$env:PATH;$((Get-Location).Path)\venv\Scripts"
        }
    }
    
    return @{ MinGW = $mingwFound; MSVC = $msvcFound }
}

# Function to reset CMake cache when switching generators
function Reset-CMakeCache {
    param([string]$BuildDir)
    
    if (Test-Path "$BuildDir\CMakeCache.txt") {
        Write-Host "Clearing CMake cache to prevent generator conflicts..." -ForegroundColor Yellow
        Remove-Item "$BuildDir\CMakeCache.txt" -Force
    }
    if (Test-Path "$BuildDir\CMakeFiles") {
        Remove-Item "$BuildDir\CMakeFiles" -Recurse -Force
    }
}

# Function to configure CMake with appropriate generator
function Invoke-CMakeConfig {
    param(
        [string]$BuildDir,
        [string]$BuildType,
        [hashtable]$Compilers
    )
    
    $configSuccess = $false
    
    # Try MinGW with Ninja first (if available)
    if ($Compilers.MinGW) {
        Write-Host "Configuring with MinGW + Ninja..." -ForegroundColor Cyan
        try {
            & cmake -S . -B $BuildDir -G "Ninja" -DCMAKE_BUILD_TYPE=$BuildType -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++
            if ($LASTEXITCODE -eq 0) {
                Write-Host "CMake configuration successful with MinGW + Ninja" -ForegroundColor Green
                $configSuccess = $true
                return "Ninja"
            }
        } catch {
            Write-Host "MinGW + Ninja configuration failed, trying alternatives..." -ForegroundColor Yellow
        }
        
        if (-not $configSuccess) {
            Reset-CMakeCache -BuildDir $BuildDir
            Write-Host "Trying MinGW with Unix Makefiles..." -ForegroundColor Cyan
            try {
                & cmake -S . -B $BuildDir -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=$BuildType -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "CMake configuration successful with MinGW + Unix Makefiles" -ForegroundColor Green
                    $configSuccess = $true
                    return "Unix Makefiles"
                }
            } catch {
                Write-Host "MinGW + Unix Makefiles configuration failed" -ForegroundColor Yellow
            }
        }
    }
    
    # Try MSVC generators if MinGW failed or not available
    if (-not $configSuccess -and $Compilers.MSVC) {
        $generators = @("Visual Studio 17 2022", "Visual Studio 16 2019")
        
        foreach ($generator in $generators) {
            Reset-CMakeCache -BuildDir $BuildDir
            Write-Host "Trying generator: $generator" -ForegroundColor Cyan
            try {
                & cmake -S . -B $BuildDir -G $generator -A x64
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "CMake configuration successful with $generator" -ForegroundColor Green
                    $configSuccess = $true
                    return $generator
                }
            } catch {
                Write-Host "$generator failed, trying next..." -ForegroundColor Yellow
            }
        }
    }
    
    if (-not $configSuccess) {
        throw "CMake configuration failed with all available generators"
    }
}

# Main execution
try {
    $BuildDir = "build"
    
    # Ensure build directory exists
    if (-not (Test-Path $BuildDir)) {
        New-Item -ItemType Directory -Path $BuildDir | Out-Null
    }
    
    # Check and install required tools
    $compilers = Ensure-Tooling
    
    # Configure CMake
    $generator = Invoke-CMakeConfig -BuildDir $BuildDir -BuildType $BuildType -Compilers $compilers
    
    # Build the project
    Write-Host "Building project with $BuildType configuration..." -ForegroundColor Cyan
    & cmake --build $BuildDir --config $BuildType
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed"
    }
    
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Output directory: $BuildDir" -ForegroundColor Yellow
    
} catch {
    Write-Host "Build failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}