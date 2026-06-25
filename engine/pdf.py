from __future__ import annotations

from weasyprint import HTML


def html_to_pdf(html: str, out_path: str) -> None:
    """Render a self-contained HTML string to a PDF file at out_path.

    This is the ONLY module permitted to import WeasyPrint.
    """
    HTML(string=html).write_pdf(out_path)
