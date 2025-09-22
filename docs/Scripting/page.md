# Scripting (Lua)

Overview
- GSCX ships an optional Lua scripting engine powered by LuaJIT via the "lupa" package. Use it to automate tasks like loading modules, preparing virtual USB, or running batch operations in the emulator loader.

Requirements
- Python dependency: lupa (LuaJIT bindings)
- Install with: pip install lupa

Where to use
- GUI: Scripting tab inside the application
- CLI: gscx_app --script path/to/script.lua [--bundle file.gscb | --load-default] [--boot-recovery]

Quick start (GUI)
1) Open the Scripting tab
2) Write a Lua script or click Load Script to open a .lua file
3) Click Run to execute, Run Selection to execute only the highlighted lines, or Run File to execute a file directly
4) Use Clear Output to clear the console output

Quick start (CLI)
- Load default modules and run a script:
  gscx_app --load-default --script my_script.lua
- Load a bundle and run a script then boot recovery:
  gscx_app --bundle GSCore.gscb --script setup.lua --boot-recovery

Lua API (table: gscx)
- print(...): Prints to the scripting output
- log(msg): Sends log to main log channel
- sleep(seconds): Pause execution for seconds
- check_cancel(): Raises error if user requested cancellation
- load_modules(): Load default DLL modules
- load_bundle(path): Load GSCore bundle (.gscb)
- boot_recovery(): Run GSCX_RecoveryEntry after modules are loaded
- setenv(key, value): Set environment variable
- getenv(key): Get environment variable
- cwd(): Get current working directory
- chdir(path): Change current working directory
- exists(path): Check if path exists
- join(a, b, ...): Join paths
- abspath(path): Absolute path
- dirname(path): Parent directory
- basename(path): File name
- listdir([path]): List directory contents
- read_text(path[, encoding]): Read text file
- write_text(path, content[, encoding]): Write text file
- mkdir(path[, exist_ok]): Create directory (recursive)

Examples
Load default modules and boot recovery:

-- example1.lua
print('GSCX scripting: boot recovery')
gscx.load_modules()
gscx.boot_recovery()

Prepare virtual USB structure in a folder:

-- example2.lua
local root = gscx.abspath('C:/GSCX/virtual_usb')
gscx.mkdir(root)
local pup = 'C:/firmwares/PS3UPDAT.PUP'
if not gscx.exists(pup) then
  error('PUP not found: '..pup)
end
-- copy PUP as PS3UPDAT.PUP
local dest = gscx.join(root, 'PS3UPDAT.PUP')
local content = gscx.read_text(pup, 'latin1') -- or use io.open in binary if needed
-- NOTE: for binary copy prefer Lua file io; this is illustrative for text ops
local f = io.open(dest, 'wb'); f:write(content); f:close()
print('Prepared at '..root)

Tips
- The engine changes the working directory to the script file's folder when running with run_file() so that relative paths work as expected
- Use gscx.check_cancel() periodically in long loops to make Stop responsive
- For binary operations, use Lua's io.open in 'rb'/'wb' mode

Troubleshooting
- If you see "Lua runtime not available", install lupa: pip install lupa
- On Windows with Python 3.12+, use wheels from PyPI; if installation fails, consider Python 3.10/3.11

Credits
- LuaJIT runtime via lupa
- PySide6 for the GUI