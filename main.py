import solid as s

from deck import LumberFactory, LumberSize
from deck_joists_on_blocks import DeckJoistsOnBlocks, LDeckOnBlocks
from flush_beam_deck import FlushBeamDeck
from footings import DeckBlockFactory
from point import Dim
from shapes import ShapeCollection
from surroundings import Ground, House
from util import ft, write_dxf_doc

TwoBySix = LumberFactory(LumberSize.TWO.value, LumberSize.SIX.value)
d = DeckJoistsOnBlocks(
    width=234 - ft(3.5),
    length=ft(16),
    height=8,
    beam_class=TwoBySix,
    beam_overhang=6,
    joist_class=TwoBySix,
    decking_class=LumberFactory(LumberSize.SIX.value, LumberSize.ONE.value),
    footing_class=DeckBlockFactory(),
    block_overhang1=8,
    block_overhang2=16
)

d2 = LDeckOnBlocks(
    width=240,
    length=ft(16),
    height=8,
    beam_class=TwoBySix,
    beam_overhang=6,
    joist_class=TwoBySix,
    decking_class=LumberFactory(LumberSize.SIX.value, LumberSize.ONE.value),
    footing_class=DeckBlockFactory(),
    cutout_x=ft(4),
    cutout_y=ft(5),
    block_overhang1=8,
    block_overhang2=16,
    block_overhang3=8
)
#
# d3 = FlushBeamDeck(
#     width=ft(16),
#     length=ft(16),
#     height=8,
#     beam_class=TwoBySix,
#     joist_class=TwoBySix,
#     decking_class=LumberFactory(LumberSize.SIX.value, LumberSize.ONE.value),
#     footing_class=DeckBlockFactory()
# )
deck_and_house = ShapeCollection([
    Ground(),
    House(),
    d2.all()
])
s.scad_render_to_file(deck_and_house.render_scad(), 'foo.scad')
write_dxf_doc(deck_and_house, Dim.Z, 'foo_top.dxf')
write_dxf_doc(deck_and_house, Dim.Y, 'foo_front.dxf')
write_dxf_doc(deck_and_house, Dim.X, 'foo_side.dxf')
