#include "gscx/c_api.h"
#include "gscx/cpp_utils.h"

#include <cstdlib>
#include <cstring>
#include <string>

using namespace gscx::util;

static char* dup_to_cstr(const std::string& s) {
    char* out = static_cast<char*>(std::malloc(s.size() + 1));
    if (!out) return nullptr;
    std::memcpy(out, s.c_str(), s.size() + 1);
    return out;
}

extern "C" {

char* gscx_util_version(void) {
    return dup_to_cstr(version());
}

char* gscx_guid_v4(void) {
    return dup_to_cstr(guid_v4());
}

uint64_t gscx_crc64(const void* bytes, size_t len) {
    if (!bytes && len) return 0ULL;
    return crc64_ecma(bytes, len);
}

void gscx_free(void* p) {
    std::free(p);
}

} // extern "C"