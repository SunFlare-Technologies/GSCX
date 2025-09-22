# GSCX Lua Scripting API Reference

## Overview

The GSCX Lua API provides comprehensive access to PlayStation 3 system emulation functionality through a clean, high-level scripting interface. This API is designed for automation, testing, system diagnostics, and custom workflow development.

## Core Modules

### gscx (Core Module)

The main GSCX module provides system-level functionality and module management.

#### Functions

##### `gscx.initialize(config?)`
Initializes the GSCX system with optional configuration.

**Parameters:**
- `config` (table, optional): System configuration
  - `log_level` (string): 'DEBUG', 'INFO', 'WARN', 'ERROR'
  - `log_file` (string): Path to log file
  - `temp_dir` (string): Temporary directory path

**Returns:**
- `boolean`: Success status

**Example:**
```lua
local success = gscx.initialize({
    log_level = 'INFO',
    log_file = 'gscx.log',
    temp_dir = './temp'
})

if not success then
    error('Failed to initialize GSCX')
end
```

##### `gscx.shutdown()`
Cleanly shuts down the GSCX system and releases all resources.

**Example:**
```lua
gscx.shutdown()
```

##### `gscx.load_module(name)`
Loads a system module by name.

**Parameters:**
- `name` (string): Module name ('syscon', 'recovery', 'bootloader', etc.)

**Returns:**
- `boolean`: Success status

**Example:**
```lua
local modules = {'syscon', 'recovery', 'bootloader'}
for _, module in ipairs(modules) do
    if not gscx.load_module(module) then
        gscx.log.error('Failed to load module: ' .. module)
    end
end
```

##### `gscx.get_version()`
Returns version information.

**Returns:**
- `table`: Version information
  - `major` (number): Major version
  - `minor` (number): Minor version
  - `patch` (number): Patch version
  - `build` (string): Build identifier

**Example:**
```lua
local version = gscx.get_version()
print(string.format('GSCX v%d.%d.%d (%s)', 
    version.major, version.minor, version.patch, version.build))
```

##### `gscx.sleep(milliseconds)`
Suspends execution for the specified duration.

**Parameters:**
- `milliseconds` (number): Sleep duration in milliseconds

**Example:**
```lua
gscx.sleep(1000)  -- Sleep for 1 second
```

### gscx.log (Logging Module)

Provides comprehensive logging functionality.

#### Functions

##### `gscx.log.debug(message)`
##### `gscx.log.info(message)`
##### `gscx.log.warn(message)`
##### `gscx.log.error(message)`
Log messages at different severity levels.

**Parameters:**
- `message` (string): Log message

**Example:**
```lua
gscx.log.info('System initialization started')
gscx.log.warn('Configuration file not found, using defaults')
gscx.log.error('Critical system failure')
```

##### `gscx.log.set_level(level)`
Sets the minimum log level.

**Parameters:**
- `level` (string): 'DEBUG', 'INFO', 'WARN', 'ERROR'

##### `gscx.log.to_file(filename)`
Enables logging to file.

**Parameters:**
- `filename` (string): Log file path

### gscx.system (System Management)

Provides system configuration and management functions.

#### Functions

##### `gscx.system.configure_hardware(config)`
Configures hardware emulation parameters.

**Parameters:**
- `config` (table): Hardware configuration
  - `model` (string): PS3 model ('CECHA01', 'CECHB01', etc.)
  - `memory_xdr` (number): XDR memory size in MB
  - `memory_gddr3` (number): GDDR3 memory size in MB
  - `cpu_threads` (number): Number of CPU threads
  - `enable_spu` (boolean): Enable SPU emulation

**Returns:**
- `boolean`: Success status

**Example:**
```lua
local config = {
    model = 'CECHA01',
    memory_xdr = 256,
    memory_gddr3 = 256,
    cpu_threads = 6,
    enable_spu = true
}

if gscx.system.configure_hardware(config) then
    gscx.log.info('Hardware configured successfully')
else
    gscx.log.error('Hardware configuration failed')
end
```

##### `gscx.system.get_status()`
Returns current system status.

**Returns:**
- `table`: System status
  - `state` (string): 'initializing', 'ready', 'booting', 'running', 'error'
  - `uptime` (number): System uptime in seconds
  - `memory_usage` (table): Memory usage statistics
  - `cpu_usage` (number): CPU usage percentage

**Example:**
```lua
local status = gscx.system.get_status()
print('System state: ' .. status.state)
print('Uptime: ' .. status.uptime .. ' seconds')
print('CPU usage: ' .. status.cpu_usage .. '%')
```

### gscx.boot (Boot Management)

Controls the PS3 boot sequence.

#### Functions

##### `gscx.boot.start(mode?)`
Starts the boot sequence.

**Parameters:**
- `mode` (string, optional): Boot mode ('normal', 'recovery', 'safe')

**Returns:**
- `boolean`: Success status

**Example:**
```lua
-- Normal boot
if gscx.boot.start() then
    gscx.log.info('Boot sequence started')
end

-- Recovery mode boot
if gscx.boot.start('recovery') then
    gscx.log.info('Recovery mode boot started')
end
```

##### `gscx.boot.get_status()`
Returns current boot status.

**Returns:**
- `string`: Boot status ('idle', 'booting', 'ready', 'error')

##### `gscx.boot.get_progress()`
Returns boot progress information.

**Returns:**
- `table`: Boot progress
  - `stage` (string): Current boot stage
  - `progress` (number): Progress percentage (0-100)
  - `description` (string): Stage description

**Example:**
```lua
while gscx.boot.get_status() == 'booting' do
    local progress = gscx.boot.get_progress()
    print(string.format('%s: %d%% - %s', 
        progress.stage, progress.progress, progress.description))
    gscx.sleep(100)
end
```

##### `gscx.boot.wait_for_completion(timeout?)`
Waits for boot completion with optional timeout.

**Parameters:**
- `timeout` (number, optional): Timeout in seconds

**Returns:**
- `boolean`: Success status

**Example:**
```lua
if gscx.boot.wait_for_completion(60) then
    gscx.log.info('Boot completed successfully')
else
    gscx.log.error('Boot timed out or failed')
end
```

### gscx.recovery (Recovery Mode)

Provides access to recovery mode functionality.

#### Functions

##### `gscx.recovery.enter()`
Enters recovery mode.

**Returns:**
- `boolean`: Success status

##### `gscx.recovery.exit()`
Exits recovery mode.

**Returns:**
- `boolean`: Success status

##### `gscx.recovery.mount_usb(path)`
Mounts a virtual USB device.

**Parameters:**
- `path` (string): Path to USB image or directory

**Returns:**
- `boolean`: Success status

**Example:**
```lua
if gscx.recovery.enter() then
    gscx.log.info('Entered recovery mode')
    
    -- Mount virtual USB with firmware
    if gscx.recovery.mount_usb('./firmware/usb_image.img') then
        gscx.log.info('USB mounted successfully')
        
        -- Wait for firmware installation
        gscx.recovery.wait_for_pup_install()
    end
    
    gscx.recovery.exit()
end
```

##### `gscx.recovery.install_firmware(pup_path)`
Installs firmware from PUP file.

**Parameters:**
- `pup_path` (string): Path to PS3UPDAT.PUP file

**Returns:**
- `boolean`: Success status

##### `gscx.recovery.run_diagnostics()`
Runs hardware diagnostics.

**Returns:**
- `table`: Diagnostic results
  - `overall_status` (string): 'pass', 'fail', 'warning'
  - `tests` (table): Individual test results

**Example:**
```lua
local diag = gscx.recovery.run_diagnostics()
print('Overall status: ' .. diag.overall_status)

for test_name, result in pairs(diag.tests) do
    print(string.format('%s: %s', test_name, result.status))
    if result.status == 'fail' then
        print('  Error: ' .. result.error)
    end
end
```

### gscx.syscon (System Controller)

Provides SYSCON virtualization interface.

#### Functions

##### `gscx.syscon.send_command(cmd, data?)`
Sends a command to the virtual SYSCON.

**Parameters:**
- `cmd` (number): Command code
- `data` (string, optional): Command data

**Returns:**
- `table`: Response
  - `status` (number): Response status
  - `data` (string): Response data

**Example:**
```lua
-- Get SYSCON version
local response = gscx.syscon.send_command(0x11)  -- GET_VERSION
if response.status == 0 then
    gscx.log.info('SYSCON version: ' .. response.data)
end
```

##### `gscx.syscon.get_temperature()`
Returns system temperature readings.

**Returns:**
- `table`: Temperature data
  - `cpu` (number): CPU temperature in Celsius
  - `rsx` (number): RSX temperature in Celsius

##### `gscx.syscon.set_fan_speed(speed)`
Sets fan speed.

**Parameters:**
- `speed` (number): Fan speed percentage (0-100)

**Returns:**
- `boolean`: Success status

### gscx.memory (Memory Management)

Provides memory access and management functions.

#### Functions

##### `gscx.memory.read(address, size)`
Reads memory from specified address.

**Parameters:**
- `address` (number): Memory address
- `size` (number): Number of bytes to read

**Returns:**
- `string`: Memory data (binary)

##### `gscx.memory.write(address, data)`
Writes data to memory address.

**Parameters:**
- `address` (number): Memory address
- `data` (string): Data to write (binary)

**Returns:**
- `boolean`: Success status

**Example:**
```lua
-- Read 4 bytes from address
local data = gscx.memory.read(0x80010000, 4)
if data then
    local value = string.unpack('<I4', data)  -- Little-endian 32-bit int
    print('Value at 0x80010000: ' .. value)
end

-- Write 4 bytes to address
local new_value = 0x12345678
local packed_data = string.pack('<I4', new_value)
if gscx.memory.write(0x80010000, packed_data) then
    gscx.log.info('Memory write successful')
end
```

##### `gscx.memory.allocate(size, alignment?)`
Allocates memory block.

**Parameters:**
- `size` (number): Size in bytes
- `alignment` (number, optional): Alignment requirement

**Returns:**
- `number`: Allocated address (0 on failure)

##### `gscx.memory.free(address)`
Frees allocated memory block.

**Parameters:**
- `address` (number): Address to free

**Returns:**
- `boolean`: Success status

### gscx.file (File System)

Provides file system access and manipulation.

#### Functions

##### `gscx.file.read(path)`
Reads entire file content.

**Parameters:**
- `path` (string): File path

**Returns:**
- `string`: File content (nil on error)

##### `gscx.file.write(path, content)`
Writes content to file.

**Parameters:**
- `path` (string): File path
- `content` (string): Content to write

**Returns:**
- `boolean`: Success status

##### `gscx.file.exists(path)`
Checks if file exists.

**Parameters:**
- `path` (string): File path

**Returns:**
- `boolean`: File exists

**Example:**
```lua
-- Read configuration file
local config_path = './config.json'
if gscx.file.exists(config_path) then
    local content = gscx.file.read(config_path)
    if content then
        local config = json.decode(content)
        -- Process configuration
    end
else
    gscx.log.warn('Configuration file not found')
end
```

### gscx.crypto (Cryptography)

Provides cryptographic functions for PS3 security.

#### Functions

##### `gscx.crypto.decrypt_self(self_data, key?)`
Decrypts SELF (Signed Executable and Linkable Format) data.

**Parameters:**
- `self_data` (string): SELF file data
- `key` (string, optional): Decryption key

**Returns:**
- `string`: Decrypted ELF data (nil on failure)

##### `gscx.crypto.verify_signature(data, signature, key)`
Verifies digital signature.

**Parameters:**
- `data` (string): Data to verify
- `signature` (string): Digital signature
- `key` (string): Public key

**Returns:**
- `boolean`: Signature valid

### gscx.network (Network Interface)

Provides network functionality for PS3 emulation.

#### Functions

##### `gscx.network.create_server(port, handler)`
Creates a network server.

**Parameters:**
- `port` (number): Port number
- `handler` (function): Connection handler function

**Returns:**
- `table`: Server object

**Example:**
```lua
local server = gscx.network.create_server(80, function(client)
    gscx.log.info('Client connected: ' .. client.address)
    
    client:send('HTTP/1.1 200 OK\r\n\r\nHello World')
    client:close()
end)

if server then
    server:start()
    gscx.log.info('HTTP server started on port 80')
end
```

## Event System

### Event Registration

```lua
-- Register event handlers
gscx.events.on('boot_progress', function(stage, progress)
    print(string.format('Boot %s: %d%%', stage, progress))
end)

gscx.events.on('system_error', function(error_code, message)
    gscx.log.error(string.format('System error %d: %s', error_code, message))
end)

gscx.events.on('hardware_event', function(component, event_type, data)
    gscx.log.debug(string.format('Hardware event: %s.%s', component, event_type))
end)
```

### Available Events

| Event Name | Parameters | Description |
|------------|------------|-------------|
| `boot_progress` | `stage`, `progress` | Boot sequence progress |
| `boot_complete` | `success`, `error?` | Boot completion |
| `system_error` | `code`, `message` | System error occurred |
| `hardware_event` | `component`, `type`, `data` | Hardware state change |
| `memory_warning` | `usage`, `limit` | Memory usage warning |
| `temperature_alert` | `component`, `temperature` | Temperature threshold exceeded |
| `recovery_entered` | - | Recovery mode activated |
| `recovery_exited` | - | Recovery mode deactivated |
| `firmware_installed` | `version`, `success` | Firmware installation result |

## Utility Functions

### String Utilities

```lua
-- Hexadecimal conversion
local hex_string = gscx.util.to_hex(data)
local binary_data = gscx.util.from_hex(hex_string)

-- Base64 encoding/decoding
local encoded = gscx.util.base64_encode(data)
local decoded = gscx.util.base64_decode(encoded)

-- CRC32 checksum
local checksum = gscx.util.crc32(data)
```

### Time Utilities

```lua
-- Get current timestamp
local timestamp = gscx.util.timestamp()

-- Format time
local formatted = gscx.util.format_time(timestamp, '%Y-%m-%d %H:%M:%S')

-- Measure execution time
local start_time = gscx.util.get_time()
-- ... code to measure ...
local elapsed = gscx.util.get_time() - start_time
print('Execution time: ' .. elapsed .. ' seconds')
```

## Advanced Examples

### Automated System Test

```lua
#!/usr/bin/env lua
-- Comprehensive system test script

local gscx = require('gscx')

-- Test configuration
local test_config = {
    models = {'CECHA01', 'CECHB01', 'CECH2001'},
    boot_modes = {'normal', 'recovery'},
    timeout = 120  -- 2 minutes
}

-- Initialize logging
gscx.initialize({
    log_level = 'INFO',
    log_file = 'system_test.log'
})

-- Test results
local results = {}

function run_test(model, boot_mode)
    gscx.log.info(string.format('Testing %s in %s mode', model, boot_mode))
    
    -- Configure hardware
    local config = {
        model = model,
        memory_xdr = 256,
        memory_gddr3 = 256,
        cpu_threads = 4
    }
    
    if not gscx.system.configure_hardware(config) then
        return false, 'Hardware configuration failed'
    end
    
    -- Start boot sequence
    if not gscx.boot.start(boot_mode) then
        return false, 'Boot start failed'
    end
    
    -- Wait for completion
    local start_time = gscx.util.get_time()
    while gscx.boot.get_status() == 'booting' do
        if gscx.util.get_time() - start_time > test_config.timeout then
            return false, 'Boot timeout'
        end
        gscx.sleep(100)
    end
    
    local final_status = gscx.boot.get_status()
    if final_status == 'ready' then
        -- Run additional tests
        local diag = gscx.recovery.run_diagnostics()
        if diag.overall_status ~= 'pass' then
            return false, 'Diagnostics failed'
        end
        
        return true, 'All tests passed'
    else
        return false, 'Boot failed: ' .. final_status
    end
end

-- Run all test combinations
for _, model in ipairs(test_config.models) do
    for _, boot_mode in ipairs(test_config.boot_modes) do
        local test_name = model .. '_' .. boot_mode
        local success, message = run_test(model, boot_mode)
        
        results[test_name] = {
            success = success,
            message = message,
            timestamp = gscx.util.timestamp()
        }
        
        if success then
            gscx.log.info(test_name .. ': PASS')
        else
            gscx.log.error(test_name .. ': FAIL - ' .. message)
        end
        
        -- Reset system between tests
        gscx.system.reset()
        gscx.sleep(1000)
    end
end

-- Generate test report
local report = {
    timestamp = gscx.util.timestamp(),
    total_tests = 0,
    passed_tests = 0,
    failed_tests = 0,
    results = results
}

for test_name, result in pairs(results) do
    report.total_tests = report.total_tests + 1
    if result.success then
        report.passed_tests = report.passed_tests + 1
    else
        report.failed_tests = report.failed_tests + 1
    end
end

-- Save report
local json = require('json')
local report_json = json.encode(report)
gscx.file.write('test_report.json', report_json)

-- Print summary
print(string.format('Test Summary: %d/%d passed (%d failed)', 
    report.passed_tests, report.total_tests, report.failed_tests))

gscx.shutdown()
```

### Performance Monitoring

```lua
-- Performance monitoring script
local gscx = require('gscx')

-- Enable profiling
gscx.profiler.enable()
gscx.profiler.set_sampling_rate(1000)  -- 1ms

-- Monitor system performance
function monitor_performance(duration)
    local start_time = gscx.util.get_time()
    local samples = {}
    
    while gscx.util.get_time() - start_time < duration do
        local status = gscx.system.get_status()
        local sample = {
            timestamp = gscx.util.get_time(),
            cpu_usage = status.cpu_usage,
            memory_usage = status.memory_usage.used / status.memory_usage.total * 100,
            temperature = gscx.syscon.get_temperature()
        }
        
        table.insert(samples, sample)
        gscx.sleep(100)  -- Sample every 100ms
    end
    
    return samples
end

-- Run performance test
gscx.log.info('Starting performance monitoring')
local samples = monitor_performance(60)  -- Monitor for 60 seconds

-- Analyze results
local cpu_avg = 0
local mem_avg = 0
local temp_max = 0

for _, sample in ipairs(samples) do
    cpu_avg = cpu_avg + sample.cpu_usage
    mem_avg = mem_avg + sample.memory_usage
    temp_max = math.max(temp_max, math.max(sample.temperature.cpu, sample.temperature.rsx))
end

cpu_avg = cpu_avg / #samples
mem_avg = mem_avg / #samples

gscx.log.info(string.format('Performance Summary:'))
gscx.log.info(string.format('  Average CPU usage: %.1f%%', cpu_avg))
gscx.log.info(string.format('  Average memory usage: %.1f%%', mem_avg))
gscx.log.info(string.format('  Maximum temperature: %.1f°C', temp_max))

-- Generate performance report
gscx.profiler.generate_report('performance_report.html')
```

## Error Handling Best Practices

### Robust Error Handling

```lua
function safe_operation()
    local success, result = pcall(function()
        -- Potentially risky operation
        return gscx.some_risky_function()
    end)
    
    if not success then
        gscx.log.error('Operation failed: ' .. tostring(result))
        return nil, result
    end
    
    return result
end

-- Usage
local result, error = safe_operation()
if not result then
    -- Handle error appropriately
    gscx.log.error('Failed to perform operation: ' .. error)
    return false
end
```

### Resource Cleanup

```lua
function with_resource(resource_func, operation_func)
    local resource = resource_func()
    if not resource then
        return nil, 'Failed to acquire resource'
    end
    
    local success, result = pcall(operation_func, resource)
    
    -- Always cleanup, even on error
    if resource.cleanup then
        resource:cleanup()
    end
    
    if not success then
        return nil, result
    end
    
    return result
end

-- Usage example
local result, error = with_resource(
    function() return gscx.memory.allocate(1024) end,
    function(memory_block)
        -- Use memory block
        gscx.memory.write(memory_block, data)
        return gscx.memory.read(memory_block, 1024)
    end
)
```

This comprehensive API reference provides all the tools needed for advanced PS3 system emulation scripting and automation.