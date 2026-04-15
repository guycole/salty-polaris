from pathlib import Path
import sys


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sample_html(name: str) -> str:
    return (_project_root() / "sample" / name).read_text(encoding="utf-8")


def _load_parser_class():
    sys.path.insert(0, str(_project_root() / "src" / "polaris_docker"))
    from vessels import VesselParser

    return VesselParser


def test_destination_locode_defaults_when_missing():
    parser_cls = _load_parser_class()
    parser = parser_cls()

    raw_html = _sample_html("ed7e60f3-9f11-4f70-8259-6ec8e64526c9.html")
    observation = parser.parse(raw_html)

    assert observation.destination_locode == "PAXXX001"
