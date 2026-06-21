from __future__ import annotations

from functools import lru_cache

from .compiler import compile_method_pack
from .models import CompiledMethodPack


@lru_cache(maxsize=1)
def load_compiled_method_pack() -> CompiledMethodPack:
    return compile_method_pack()
