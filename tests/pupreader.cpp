#include <iostream>
#include <fstream>
#include <vector>
#include <cstdint>
#include <string>

struct Entry {
    uint32_t id;
    uint64_t offset;
    uint64_t size;
};


int main(int argc, char* argv[]) {   // <-- TEM QUE SER ESSE MAIN
    if (argc < 2) {
        std::cerr << "Uso: " << argv[0] << " <arquivo PUP>\n";
        return 1;
    }

    std::ifstream file(argv[1], std::ios::binary);
    if (!file) {
        std::cerr << "Erro ao abrir " << argv[1] << "\n";
        return 1;
    }

    char magic[8];
    file.read(magic, 8);
    if (std::string(magic, 5) != "SCEUF") {
        std::cerr << "Arquivo inválido\n";
        return 1;
    }

    uint64_t version, fileCount;
    file.read(reinterpret_cast<char*>(&version), 8);
    file.read(reinterpret_cast<char*>(&fileCount), 8);

    std::cout << "Versão do PUP: " << std::hex << version << std::dec << "\n";
    std::cout << "Número de arquivos internos: " << fileCount << "\n";

    std::vector<Entry> entries;
    for (size_t i = 0; i < fileCount; i++) {
        Entry e;
        uint32_t padding;
        file.read(reinterpret_cast<char*>(&e.id), 4);
        file.read(reinterpret_cast<char*>(&padding), 4);
        file.read(reinterpret_cast<char*>(&e.offset), 8);
        file.read(reinterpret_cast<char*>(&e.size), 8);
        entries.push_back(e);
    }

    for (const auto &e : entries) {
        std::cout << "ID: " << std::hex << e.id 
                  << " Offset: " << std::dec << e.offset 
                  << " Size: " << e.size << " bytes\n";
    }

    return 0;
}
