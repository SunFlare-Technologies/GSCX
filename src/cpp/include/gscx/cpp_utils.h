#pragma once
#include <cstdint>
#include <cstddef>
#include <string>

namespace gscx {
namespace util {

// Returns semantic version string of the native library
std::string version();

// Generates a random UUID v4 string (lowercase hex)
std::string guid_v4();

// CRC64-ECMA calculation over a byte buffer
std::uint64_t crc64_ecma(const void* data, std::size_t len);

} // namespace util
} // namespace gscx