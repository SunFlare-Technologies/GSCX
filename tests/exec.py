import struct

def parse_pup(filename):
    with open(filename, "rb") as f:
        magic = f.read(8)
        if magic[:5] != b"SCEUF":
            raise ValueError("Arquivo não parece ser um PS3UPDAT.PUP válido")

        # lê versão do header
        version = struct.unpack(">Q", f.read(8))[0]

        # número de arquivos dentro
        file_count = struct.unpack(">Q", f.read(8))[0]

        print(f"Versão do PUP: {version}")
        print(f"Número de arquivos internos: {file_count}")

        # pula até tabela de arquivos
        entries = []
        for i in range(file_count):
            file_id = struct.unpack(">I", f.read(4))[0]
            f.read(4)  # padding
            offset = struct.unpack(">Q", f.read(8))[0]
            size = struct.unpack(">Q", f.read(8))[0]
            entries.append((file_id, offset, size))

        print("\nArquivos internos:")
        for eid, off, sz in entries:
            print(f"  ID: {eid:08X}, Offset: {off}, Tamanho: {sz} bytes")

        # tenta achar o version.txt e license (se existirem)
        for eid, off, sz in entries:
            f.seek(off)
            data = f.read(sz)
            if b"release:" in data or b"system software" in data:
                print("\n[Version.txt detectado]:")
                print(data.decode(errors="ignore"))
            if b"Copyright" in data or b"Sony Computer Entertainment" in data:
                print("\n[Legal Notice detectado]:")
                print(data.decode(errors="ignore"))


if __name__ == "__main__":
    parse_pup("tests\PS3UPDAT.PUP")
