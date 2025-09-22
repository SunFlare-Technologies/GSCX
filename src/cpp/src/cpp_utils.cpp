#include "gscx/cpp_utils.h"

#include <array>
#include <random>
#include <sstream>
#include <iomanip>

namespace gscx { namespace util {

std::string version() {
    // Keep in sync with app-level version; can be wired to app.ini later
    return "0.4.1-alpha";
}

static inline void uuid_set_version_variant(std::array<unsigned char,16>& b) {
    // Set version (4)
    b[6] = static_cast<unsigned char>((b[6] & 0x0F) | 0x40);
    // Set variant (10xxxxxx)
    b[8] = static_cast<unsigned char>((b[8] & 0x3F) | 0x80);
}

std::string guid_v4() {
    std::random_device rd;
    std::mt19937_64 gen(rd());
    std::uniform_int_distribution<unsigned long long> dist;

    std::array<unsigned char, 16> bytes{};
    for (int i = 0; i < 16; i += 8) {
        auto v = dist(gen);
        for (int j = 0; j < 8; ++j) {
            bytes[i + j] = static_cast<unsigned char>((v >> (j * 8)) & 0xFF);
        }
    }

    uuid_set_version_variant(bytes);

    std::ostringstream oss;
    oss << std::hex << std::setfill('0');
    for (int i = 0; i < 16; ++i) {
        oss << std::setw(2) << static_cast<int>(bytes[i]);
        if (i == 3 || i == 5 || i == 7 || i == 9) oss << '-';
    }
    return oss.str();
}

// CRC64-ECMA polynomial
static constexpr std::uint64_t CRC64_POLY = 0x42F0E1EBA9EA3693ULL;

static const std::uint64_t* crc_table() {
    static std::uint64_t table[256];
    static bool inited = false;
    if (!inited) {
        for (std::uint64_t i = 0; i < 256; ++i) {
            std::uint64_t crc = i << 56;
            for (int j = 0; j < 8; ++j) {
                if (crc & 0x8000000000000000ULL) crc = (crc << 1) ^ CRC64_POLY;
                else crc <<= 1;
            }
            table[i] = crc;
        }
        inited = true;
    }
    return table;
}

std::uint64_t crc64_ecma(const void* data, std::size_t len) {
    const auto* tbl = crc_table();
    const unsigned char* p = static_cast<const unsigned char*>(data);
    std::uint64_t crc = 0ULL; // ECMA-182 initial value is 0
    while (len--) {
        std::uint8_t idx = static_cast<std::uint8_t>((crc >> 56) ^ *p++);
        crc = tbl[idx] ^ (crc << 8);
    }
    // ECMA-182 does not require final XOR
    return crc;
}

}} // namespace gscx::util