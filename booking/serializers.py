from pathlib import Path

_source = Path(__file__).resolve().parent.parent / "serializers.py"
exec(compile(_source.read_text(encoding="utf-8"), str(_source), "exec"))
