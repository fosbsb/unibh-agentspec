import re
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"
TOKENS = STATIC / "css" / "tokens.css"

DESIGN_SYSTEM_COLORS = {
    "--cor-preto": "#0D0D0D",
    "--cor-laranja": "#FF7A00",
    "--cor-amarelo": "#FFC20E",
    "--cor-vermelho": "#D62828",
    "--cor-superficie": "#1C1C1C",
    "--cor-superficie-alta": "#2A2A2A",
    "--cor-borda": "#3D3D3D",
    "--cor-texto": "#FFFFFF",
    "--cor-texto-suave": "#BDBDBD",
    "--cor-vermelho-claro": "#FF5A5A",
}

HEX = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
VAR_USE = re.compile(r"var\((--[a-z0-9-]+)\)")


def static_files(exclude_tokens=True):
    for path in STATIC.rglob("*"):
        if path.suffix in {".css", ".js", ".html"} and not (
            exclude_tokens and path == TOKENS
        ):
            yield path


def test_tokens_define_every_design_system_color():
    css = TOKENS.read_text(encoding="utf-8")
    for name, value in DESIGN_SYSTEM_COLORS.items():
        assert re.search(rf"{re.escape(name)}:\s*{value};", css, re.IGNORECASE), name


def test_no_hexadecimal_colors_outside_tokens():
    offenders = {
        str(path.relative_to(STATIC)): HEX.findall(path.read_text(encoding="utf-8"))
        for path in static_files()
        if HEX.search(path.read_text(encoding="utf-8"))
    }
    assert offenders == {}


def test_every_variable_used_is_defined_in_tokens():
    defined = set(re.findall(r"(--[a-z0-9-]+):", TOKENS.read_text(encoding="utf-8")))
    used = set()
    for path in static_files(exclude_tokens=False):
        used |= set(VAR_USE.findall(path.read_text(encoding="utf-8")))
    assert used - defined == set()


def test_reduced_motion_is_respected():
    css = (STATIC / "css" / "components.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in css
