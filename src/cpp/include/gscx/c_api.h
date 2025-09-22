#pragma once
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// Returns a newly-allocated UTF-8 string with the native library version.
// Caller MUST free with gscx_free().
char* gscx_util_version(void);

// Returns a newly-allocated UTF-8 string with a random UUID v4.
// Caller MUST free with gscx_free().
char* gscx_guid_v4(void);

// Computes CRC64-ECMA of a byte buffer.
uint64_t gscx_crc64(const void* bytes, size_t len);

// Frees memory returned by functions in this C API.
void gscx_free(void* p);

#ifdef __cplusplus
} // extern "C"
#endif