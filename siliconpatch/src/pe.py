"""PE parsing and SiliconPatch hook decoding."""
import collections
import hashlib
import math
from pathlib import Path
import struct


class PE:
    def __init__(self, path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        if self.data[:2] != b'MZ':
            raise ValueError('not MZ')
        self.nt = self.u32(0x3c)
        if self.data[self.nt:self.nt+4] != b'PE\0\0':
            raise ValueError('not PE')
        self.opt = self.nt + 24
        self.plus = self.u16(self.opt) == 0x20b
        if self.u16(self.opt) not in (0x10b, 0x20b):
            raise ValueError('unsupported optional header')
        self.base = self.unpack('Q' if self.plus else 'I', self.opt + (24 if self.plus else 28))[0]
        self.size = self.u32(self.opt+56)
        dd = self.opt + (112 if self.plus else 96)
        self.dirs = [self.unpack('II', dd+i*8) for i in range(min(16, self.u32(dd-4)))]
        self.sections = []
        sec = self.opt + self.u16(self.nt+20)
        for i in range(self.u16(self.nt+6)):
            off = sec+i*40
            vs, va, rs, rp = self.unpack('IIII', off+8)
            chunk = self.data[rp:rp+rs]
            counts = collections.Counter(chunk)
            entropy = -sum((n/len(chunk))*math.log2(n/len(chunk)) for n in counts.values()) if chunk else 0
            self.sections.append(dict(name=self.data[off:off+8].split(b'\0')[0].decode(errors='replace'),
                                      rva=va, virtual_size=vs, raw_size=rs, raw_offset=rp,
                                      flags=self.u32(off+36), entropy=round(entropy, 3)))

    def unpack(self, fmt, off):
        return struct.unpack_from('<'+fmt, self.data, off)

    def u32(self, off):
        return self.unpack('I', off)[0]

    def u16(self, off):
        return self.unpack('H', off)[0]

    def offset(self, rva):
        if rva < self.u32(self.opt+60):
            return rva
        for s in self.sections:
            if s['rva'] <= rva < s['rva'] + s['raw_size']:
                return s['raw_offset'] + rva-s['rva']
        raise ValueError(f'RVA {rva:#x} has no file bytes')

    def cstr(self, rva):
        off = self.offset(rva)
        return self.data[off:self.data.index(b'\0', off)].decode(errors='replace')

    def imports(self):
        rva, size = self.dirs[1]
        result = []
        if not rva:
            return result
        off = self.offset(rva)
        for i in range(4096):
            orig, stamp, chain, name, iat = self.unpack('IIIII', off+i*20)
            if not any((orig, stamp, chain, name, iat)):
                break
            entries = []
            ptr = self.offset(orig or iat)
            width = 8 if self.plus else 4
            for j in range(65536):
                value = self.unpack('Q' if self.plus else 'I', ptr+j*width)[0]
                if not value:
                    break
                symbol = f'#{value & 0xffff}' if value & (1 << (width*8-1)) else self.cstr(value+2)
                entries.append(dict(name=symbol, iat_va=hex(self.base+iat+j*width)))
            result.append(dict(dll=self.cstr(name), symbols=entries))
        return result

    def exports(self):
        rva, size = self.dirs[0]
        if not rva:
            return []
        off = self.offset(rva)
        ordinal, nf, nn, funcs, names, ords = self.unpack('IIIIII', off+16)
        result = []
        for i in range(nn):
            name = self.cstr(self.u32(self.offset(names)+i*4))
            idx = self.u16(self.offset(ords)+i*2)
            fn = self.u32(self.offset(funcs)+idx*4)
            result.append(dict(name=name, ordinal=ordinal+idx, rva=hex(fn),
                               forwarder=self.cstr(fn) if rva <= fn < rva+size else None))
        return result

    def relocations(self):
        rva, size = self.dirs[5]
        result = []
        if not rva:
            return result
        off, end = self.offset(rva), self.offset(rva)+size
        while off < end:
            page, length = self.unpack('II', off)
            if length < 8 or length % 2 or off+length > end:
                raise ValueError(f'malformed relocation block at {off:#x}')
            for pos in range(off+8, off+length, 2):
                val = self.u16(pos)
                result.append((val >> 12, page+(val & 0xfff)))
            off += length
        return result

    def summary(self):
        rel = self.relocations()
        bysec = collections.Counter()
        for typ, rva in rel:
            if typ:
                bysec.update(next((s['name'] for s in self.sections if s['rva'] <= rva < s['rva']+max(s['virtual_size'], s['raw_size'])), '<outside>') for _ in [0])
        tls = None
        if self.dirs[9][0]:
            off = self.offset(self.dirs[9][0])
            vals = self.unpack('QQQQII' if self.plus else 'IIIIII', off)
            tls = dict(zip(['start_va','end_va','index_va','callbacks_va','zero_fill','flags'], map(hex, vals)))
            callbacks = []
            if vals[3]:
                pos = self.offset(vals[3]-self.base)
                for i in range(64):
                    val = self.unpack('Q' if self.plus else 'I', pos+i*(8 if self.plus else 4))[0]
                    if not val:
                        break
                    callbacks.append(hex(val))
            tls['callbacks'] = callbacks
        return dict(path=str(self.path.resolve()), size=len(self.data), sha256=hashlib.sha256(self.data).hexdigest(),
                    md5=hashlib.md5(self.data).hexdigest(), machine=hex(self.u16(self.nt+4)),
                    timestamp=self.u32(self.nt+8), image_base=hex(self.base), image_size=hex(self.size),
                    entry_rva=hex(self.u32(self.opt+16)), characteristics=hex(self.u16(self.nt+22)),
                    dll_characteristics=hex(self.u16(self.opt+70)),
                    directories=[dict(index=i,rva=hex(a),size=b) for i,(a,b) in enumerate(self.dirs) if a or b],
                    sections=self.sections, imports=self.imports(), exports=self.exports(), tls=tls,
                    reloc_types=dict(collections.Counter(t for t,r in rel)), reloc_by_section=dict(bysec))


def hooks(pe):
    """Find adjacent immediate arguments followed by CALL to the jump writer.

    This deliberately covers one known initializer idiom, not arbitrary hooks
    or every way a DLL can modify code. Scan executable sections only.
    """
    rows = []
    for section in pe.sections:
        if not section['flags'] & 0x20000000:
            continue
        start = section['raw_offset']
        end = start + section['raw_size']
        for offset in range(start, end - 19):
            data = pe.data
            if (data[offset:offset+4] != b'\xc7\x44\x24\x04' or
                    data[offset+8:offset+11] != b'\xc7\x04\x24' or
                    data[offset+15] != 0xe8):
                continue
            replacement = pe.u32(offset+4)
            target = pe.u32(offset+11)
            if not (0x400000 <= target < 0x1000000 and
                    pe.base <= replacement < pe.base+pe.size):
                continue
            call = pe.base + section['rva'] + offset-start+15
            helper = (call+5+struct.unpack_from('<i', data, offset+16)[0]) & 0xffffffff
            rows.append(dict(target=hex(target), replacement=hex(replacement),
                             initializer_call_va=hex(call), call_file_offset=hex(offset+15),
                             jump_writer_va=hex(helper)))
    return rows
