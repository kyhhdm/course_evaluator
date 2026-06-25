from engine.pdf import html_to_pdf


def test_html_to_pdf_writes_nonempty_pdf(tmp_path):
    out = tmp_path / "out.pdf"
    html_to_pdf("<html><body><h1>Hello</h1></body></html>", str(out))
    assert out.exists()
    data = out.read_bytes()
    assert len(data) > 0
    assert data[:4] == b"%PDF"
