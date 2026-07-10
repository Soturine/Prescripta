from __future__ import annotations

import textwrap


class SimplePDFRenderer:
    def render(self, lines: list[str]) -> bytes:
        pages = self._paginate(lines)
        objects: list[bytes] = []
        page_ids: list[int] = []
        content_ids: list[int] = []
        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        objects.append(b"")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        next_id = 4
        for page_lines in pages:
            page_id = next_id
            content_id = next_id + 1
            next_id += 2
            page_ids.append(page_id)
            content_ids.append(content_id)
            objects.append(
                (
                    f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                    f"/Resources << /Font << /F1 3 0 R >> >> "
                    f"/Contents {content_id} 0 R >>"
                ).encode("ascii")
            )
            stream = self._content_stream(page_lines)
            objects.append(
                b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
                + stream
                + b"\nendstream"
            )
        kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")
        return self._build_pdf(objects)

    def _paginate(self, lines: list[str]) -> list[list[str]]:
        wrapped: list[str] = []
        for line in lines:
            if not line:
                wrapped.append("")
                continue
            wrapped.extend(textwrap.wrap(line, width=92) or [""])
        pages = [wrapped[index : index + 48] for index in range(0, len(wrapped), 48)]
        return pages or [["Relatorio Prescripta"]]

    def _content_stream(self, lines: list[str]) -> bytes:
        content = ["BT", "/F1 10 Tf", "50 800 Td", "14 TL"]
        for line in lines:
            content.append(f"({self._escape(line)}) Tj")
            content.append("T*")
        content.append("T*")
        content.append(
            f"({self._escape('Documento gerado pelo Prescripta para revisão humana.')}) Tj"
        )
        content.append("ET")
        return "\n".join(content).encode("cp1252")

    def _escape(self, value: str) -> str:
        safe = self._sanitize_text(value)
        safe.encode("cp1252")
        return safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def _sanitize_text(self, value: str) -> str:
        return value.translate(
            str.maketrans(
                {
                    "–": "-",
                    "—": "-",
                    "•": "*",
                    "“": '"',
                    "”": '"',
                    "‘": "'",
                    "’": "'",
                }
            )
        )

    def _build_pdf(self, objects: list[bytes]) -> bytes:
        output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for index, body in enumerate(objects, start=1):
            offsets.append(len(output))
            output.extend(f"{index} 0 obj\n".encode("ascii"))
            output.extend(body)
            output.extend(b"\nendobj\n")
        xref_offset = len(output)
        output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        output.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        output.extend(
            (
                "trailer\n"
                f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
                "startxref\n"
                f"{xref_offset}\n"
                "%%EOF\n"
            ).encode("ascii")
        )
        return bytes(output)
