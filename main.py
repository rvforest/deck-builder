import solid as s

from deck import LumberFactory, LumberSize
from l_deck import LDeckOnBlocks
from footings import DeckBlockFactory
from point import Dim
from shapes import ShapeCollection
from surroundings import Ground, House
from util import ft, write_dxf_doc

TwoBySix = LumberFactory(LumberSize.TWO.value, LumberSize.SIX.value)
TwoByEight = LumberFactory(LumberSize.TWO.value, LumberSize.EIGHT.value)
TrexBoard = LumberFactory(LumberSize.SIX.value, 0.94, color=(164 / 256, 132 / 256, 96 / 256))

d2 = LDeckOnBlocks(
    width=240,
    length=ft(16),
    height=8,
    beam_class=TwoBySix,
    beam_overhang=6,
    joist_class=TwoBySix,
    outer_joist_class=TwoByEight,
    decking_board_class=TrexBoard,
    footing_class=DeckBlockFactory(),
    cutout_x=ft(4),
    cutout_y=ft(5),
    block_overhang1=8,
    block_overhang2=16,
    block_overhang3=8
)
deck_and_house = ShapeCollection([
    Ground(),
    House(),
    d2.all(show_decking=True)
])
s.scad_render_to_file(deck_and_house.render_scad(), 'foo.scad')
write_dxf_doc(deck_and_house, Dim.Z, 'foo_top.dxf')
write_dxf_doc(deck_and_house, Dim.Y, 'foo_front.dxf')
write_dxf_doc(deck_and_house, Dim.X, 'foo_side.dxf')
