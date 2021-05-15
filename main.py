import solid as s

from colors import BROWN
from deck import LumberFactory, LumberSize
from l_deck import LDeckOnBlocks
from footings import DeckBlockFactory
from lumber import DeckingFactory
from point import Dim
from shapes import ShapeCollection
from surroundings import Ground, House
from util import ft, write_dxf_doc

TwoBySix = LumberFactory(LumberSize.TWO.value, LumberSize.SIX.value)
TwoByEight = LumberFactory(LumberSize.TWO.value, LumberSize.EIGHT.value)
TrexBoard = DeckingFactory(LumberSize.SIX.value, 0.94, color=BROWN)

d2 = LDeckOnBlocks(
    block_overhang1=8,
    block_overhang2=8,
    block_overhang3=8,
    cutout_x=42,
    cutout_y=ft(4) + 11,
    width=ft(19.5),
    length=ft(16) - 3,
    height=8,
    beam_class=TwoBySix,
    joist_overhang=16,
    beam_overhang=6,
    joist_class=TwoBySix,
    outer_joist_class=TwoBySix,
    decking_board_class=TrexBoard,
    footing_class=DeckBlockFactory()
)
deck_and_house = ShapeCollection([
    Ground(),
    House(),
    d2.all(show_decking=True, show_frame=True)
])
s.scad_render_to_file(deck_and_house.render_scad(), 'foo.scad')
write_dxf_doc(deck_and_house, Dim.Z, 'foo_top.dxf')
write_dxf_doc(deck_and_house, Dim.Y, 'foo_front.dxf')
write_dxf_doc(deck_and_house, Dim.X, 'foo_side.dxf')
