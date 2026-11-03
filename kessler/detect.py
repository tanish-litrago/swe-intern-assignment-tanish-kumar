"""Pick the layout parser from the table header words. Unknown layouts fail loudly (no guessing)."""
from . import layout_v1, layout_v2
from .helpers import UnknownLayout


def detect(pdf):
    words = {w["text"] for w in pdf.pages[0].extract_words(x_tolerance=1)}
    if "Kessler" not in words:
        raise UnknownLayout("supplier not recognised (no 'Kessler' on page 1)")
    if layout_v1.HEADER_WORDS <= words:
        return layout_v1
    if layout_v2.HEADER_WORDS <= words:
        return layout_v2
    raise UnknownLayout("Kessler document, but the table header matches no known layout")
