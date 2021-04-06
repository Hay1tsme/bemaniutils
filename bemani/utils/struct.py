import argparse
import pefile  # type: ignore
import struct
import sys
from typing import Optional, Tuple, List, Any


class StructPrinter:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pe = pefile.PE(data=data, fast_load=True)

    def parse_format_spec(self, fmt: str) -> Tuple[str, List[Any]]:
        prefix: str = ""
        cur_accum: str = ""
        specs: List[Any] = []
        in_prefix: bool = True
        in_dereference: bool = False
        parens: int = 0

        for c in fmt:
            if in_prefix:
                # Remember byte ordering prefix.
                if c in ["@", "=", "<", ">", "!"]:
                    prefix += c
                    continue
                else:
                    in_prefix = False

            if c == "*":
                if parens == 0:
                    # Track if we're in a dereference section.
                    if not in_dereference:
                        in_dereference = True
                        if cur_accum:
                            raise Exception("Cannot have dereference marker in middle of specifier!")
                    else:
                        # Double-indirect dereference.
                        cur_accum += c
                else:
                    # Just add it, its part of a subsection.
                    cur_accum += c
                continue

            if c == "(":
                # Clump together format specs inside parens.
                if not in_dereference:
                    raise Exception("Cannot have parenthesis in middle of specifier!")
                if parens > 0:
                    cur_accum += c

                parens += 1
                continue

            if c == ")":
                # If we hit the end of a paren, we gotta recursively parse.
                if not in_dereference:
                    raise Exception("Cannot have parenthesis in middle of specifier!")
                parens -= 1
                if parens > 0:
                    cur_accum += c
                else:
                    # Parse the accumulated data as its own format spec.
                    _, subspec = self.parse_format_spec(cur_accum)
                    cur_accum = ""
                    in_dereference = False
                    specs.append(subspec)

                continue

            if c.isdigit():
                cur_accum += c
                continue

            if c == "&":
                if cur_accum:
                    raise Exception("Hex specifier should be at beginning of specifier!")
                cur_accum += c
                continue

            cur_accum += c

            # If we're dereferencing, still do the subparse even though its only one thing.
            if parens == 0:
                if in_dereference:
                    _, subspec = self.parse_format_spec(cur_accum)
                    specs.append(subspec)
                    in_dereference = False
                else:
                    specs.append(cur_accum)

                cur_accum = ""

        return prefix, specs

    def virtual_to_physical(self, offset: int) -> int:
        for section in self.pe.sections:
            start = section.VirtualAddress + self.pe.OPTIONAL_HEADER.ImageBase
            end = start + section.SizeOfRawData

            if offset >= start and offset < end:
                return (offset - start) + section.PointerToRawData
        raise Exception(f'Couldn\'t find raw offset for virtual offset 0x{offset:08x}')

    def parse_struct(self, startaddr: str, endaddr: str, countstr: str, fmt: str) -> List[Any]:
        start: int = int(startaddr, 16)
        end: Optional[int] = int(endaddr, 16) if endaddr is not None else None
        count: Optional[int] = int(countstr, 16 if "0x" in countstr else 10) if countstr is not None else None

        if end is None and count is None:
            raise Exception("Can't handle endless structures!")
        if end is not None and count is not None:
            raise Exception("Can't handle providing two ends!")

        if start >= self.pe.OPTIONAL_HEADER.ImageBase:
            # Assume this is virtual
            start = self.virtual_to_physical(start)

        if end is not None and end >= self.pe.OPTIONAL_HEADER.ImageBase:
            # Assume this is virtual
            end = self.virtual_to_physical(end)

        # Parse out any dereference instructions.
        prefix, specs = self.parse_format_spec(fmt)

        return self.__parse_struct(start, end, count, prefix, specs)

    def __parse_struct(self, start: int, end: Optional[int], count: Optional[int], prefix: str, specs: List[Any]) -> List[Any]:
        # Now, parse out each chunk.
        output = []
        offset = start
        while True:
            if end is not None:
                if offset >= end:
                    break
            if count is not None:
                if count <= 0:
                    break
                count -= 1

            line = []
            for spec in specs:
                if isinstance(spec, str):
                    if spec[0] == "&":
                        dohex = True
                        spec = spec[1:]
                    else:
                        dohex = False

                    if spec == "z":
                        # Null-terminated string
                        bs = b""
                        while self.data[offset:(offset + 1)] != b"\x00":
                            bs += self.data[offset:(offset + 1)]
                            offset += 1
                        # Advance past null byte
                        offset += 1

                        # Hex makes no sense here
                        if dohex:
                            raise Exception("Cannot display string as hex!")
                        line.append(bs.decode('ascii'))
                    else:
                        size = struct.calcsize(prefix + spec)
                        chunk = self.data[offset:(offset + size)]
                        if spec != 'x':
                            if dohex:
                                line.append(hex(struct.unpack(prefix + spec, chunk)[0]))
                            else:
                                line.append(struct.unpack(prefix + spec, chunk)[0])
                        offset += size
                else:
                    chunk = self.data[offset:(offset + 4)]
                    pointer = struct.unpack(prefix + "I", chunk)[0]
                    offset += 4

                    # Resolve the physical address of this pointer, trick the substructure into
                    # parsing only one iteration.
                    if pointer == 0x0:
                        # Null pointer
                        line.append(None)
                    else:
                        pointer = self.virtual_to_physical(pointer)
                        subparse = self.__parse_struct(pointer, pointer + 1, None, prefix, spec)
                        if len(subparse) != 1:
                            raise Exception("Logic error!")
                        line.append(subparse[0])

            output.append(line)

        return output


def main() -> int:
    parser = argparse.ArgumentParser(description="A utility to print structs out of a DLL.")
    parser.add_argument(
        "--file",
        help="DLL file to extract from.",
        type=str,
        default=None,
        required=True,
    )
    parser.add_argument(
        "--start",
        help="Hex offset into the file we should start at.",
        type=str,
        default=None,
        required=True,
    )
    parser.add_argument(
        "--end",
        help="Hex offset into the file we should go until. Alternatively you can use --count",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--count",
        help="Number of entries to parse, as a decimal or hex integer. Alternatively you can use --end",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--format",
        help=(
            "Python struct format we should print using. See https://docs.python.org/3/library/struct.html "
            "for details. Additionally, prefixing a format specifier with * allows dereferencing pointers. "
            "Surround a chunk of format specifiers with parenthesis to dereference complex structures. For "
            "ease of unpacking C string pointers, the specifier \"z\" is recognzied to mean null-terminated "
            "string. A & preceeding a format specifier means that we should convert to hex before displaying."
        ),
        type=str,
        default=None,
        required=True,
    )
    args = parser.parse_args()

    if args.end is None and args.count is None:
        print("You must specify either an --end or a --count!", file=sys.stderr)
        return 1
    if args.end is not None and args.count is not None:
        print("You cannot specify both an --end and a --count!", file=sys.stderr)
        return 1

    fp = open(args.file, 'rb')
    data = fp.read()
    fp.close()

    def __str(obj: object) -> str:
        if obj is None:
            return "NULL"
        elif isinstance(obj, list):
            if len(obj) == 1:
                return __str(obj[0])
            else:
                return f"({', '.join(__str(o) for o in obj)})"
        else:
            return repr(obj)

    printer = StructPrinter(data)
    lines = printer.parse_struct(args.start, args.end, args.count, args.format)
    for line in lines:
        print(", ".join(__str(entry) for entry in line))

    return 0


if __name__ == '__main__':
    sys.exit(main())
