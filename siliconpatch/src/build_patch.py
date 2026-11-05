#!/usr/bin/env python3
"""Apply the Whitemane SkinLevels patch to the exact preview SiliconPatch DLL."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from pe import PE, hooks

PREVIEW_SHA256 = '2a845570706db093b2937057946e0c79b584d017f5d1eb2e9164c3da8ce70473'


SITES = (
    (0x6236a5ef, '0fb7500889542410', 'edx'),
    (0x6236a6ba, '0fb7500889542410', 'edx'),
    (0x6239df42, '0fb74008c744244400000000', 'eax'),
    (0x6239e0c0, '0fb74008c744244400000000', 'eax'),
)


def jump(source, target):
    return b'\xe9'+struct.pack('<i', target-source-5)


def pe_checksum(data, checksum_offset):
    copy = bytearray(data)
    copy[checksum_offset:checksum_offset+4] = b'\0'*4
    if len(copy) % 2:
        copy.append(0)
    total = sum(struct.unpack('<'+'H'*(len(copy)//2), copy))
    while total >> 16:
        total = (total & 0xffff)+(total >> 16)
    return total+len(data)


def build_bytes(source):
    pe = PE(source)
    if hashlib.sha256(pe.data).hexdigest() != PREVIEW_SHA256:
        raise ValueError('requires exact pristine preview source hash')
    if pe.dirs[4] != (0, 0) or pe.u32(pe.opt+64) != pe_checksum(pe.data, pe.opt+64):
        raise ValueError('unexpected signature or PE checksum')
    text = pe.sections[0]
    if text['name'] != '.text' or text['virtual_size'] != 0x5e2b0 or text['flags'] != 0x60000060:
        raise ValueError('unexpected text-section baseline')
    padding_offset = text['raw_offset']+text['virtual_size']
    if pe.data[padding_offset:text['raw_offset']+text['raw_size']] != b'\0'*336:
        raise ValueError('text padding has changed')
    data = bytearray(pe.data)
    cursor = text['virtual_size']
    patches = []
    relocations = [rva for kind, rva in pe.relocations() if kind]
    for site, expected_hex, destination in SITES:
        expected = bytes.fromhex(expected_hex)
        offset = pe.offset(site-pe.base)
        if pe.data[offset:offset+len(expected)] != expected:
            raise ValueError(f'unexpected instructions at {site:#x}')
        if any(site-pe.base <= rva < site-pe.base+len(expected) for rva in relocations):
            raise ValueError('patch intersects a relocation')
        cursor = (cursor+15) & ~15
        cave = pe.base+text['rva']+cursor
        if destination == 'edx':
            # Preserve flags and ECX. EAX remains the submesh pointer. Restore
            # ESP before replaying the original stack-relative store.
            stub = bytes.fromhex(
                '9c51'           # pushfd; push ecx
                '8b10'           # mov edx,[eax]
                '81e20000ffff'   # and edx,0xffff0000
                '0fb74808'       # movzx ecx,word[eax+8]
                '09ca'           # or edx,ecx
                '599d'           # pop ecx; popfd
                '89542410')      # mov [esp+0x10],edx
        else:
            # Preserve EDX and flags; EAX is the original instruction's result.
            stub = bytes.fromhex(
                '9c52'           # pushfd; push edx
                '8b10'           # mov edx,[eax]
                '81e20000ffff'   # and edx,0xffff0000
                '0fb74008'       # movzx eax,word[eax+8]
                '09d0'           # or eax,edx
                '5a9d'           # pop edx; popfd
                'c744244400000000')  # replay mov dword [esp+0x44],0
        resume = site+len(expected)
        stub += jump(cave+len(stub), resume)
        if cursor+len(stub) > text['raw_size']:
            raise ValueError('insufficient verified padding')
        if any(text['rva']+cursor <= rva < text['rva']+cursor+len(stub) for rva in relocations):
            raise ValueError('stub intersects a relocation')
        data[text['raw_offset']+cursor:text['raw_offset']+cursor+len(stub)] = stub
        replacement = jump(site, cave)+b'\x90'*(len(expected)-5)
        data[offset:offset+len(expected)] = replacement
        patches.append(dict(site_va=hex(site), file_offset=hex(offset), original=expected.hex(),
                            replacement=replacement.hex(), stub_va=hex(cave),
                            stub=stub.hex(), resume_va=hex(resume)))
        cursor += len(stub)
    section_header = pe.opt+pe.u16(pe.nt+20)
    struct.pack_into('<I', data, section_header+8, cursor)
    struct.pack_into('<I', data, pe.opt+64, pe_checksum(data, pe.opt+64))
    return bytes(data), dict(source_sha256=PREVIEW_SHA256,
                             candidate_sha256=hashlib.sha256(data).hexdigest(),
                             size=len(data), patches=patches,
                             original_text_virtual_size=hex(text['virtual_size']),
                             candidate_text_virtual_size=hex(cursor),
                             recovered_hooks_retained=len(hooks(pe)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data, manifest = build_bytes(args.source)
    if args.output.resolve() == args.source.resolve():
        raise ValueError('output must be separate from source')
    with args.output.open('xb') as stream:
        stream.write(data)
    manifest['filename'] = args.output.name
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
