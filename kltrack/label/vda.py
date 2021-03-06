import cairo

from kltrack.label.base import *

from gi.repository import Pango, PangoCairo

class KLTLabel(object):
    width = 210000
    height = 74000
    def __init__(self):
        self.fields = [
                (TextField(0, 0, 57000, 15000, '(1) Warenempfänger-Kurzadresse'), None),
                (TextField(57000, 0, 65000, 15000, '(2) Abladestelle - Lagerort - Verwendungsschlüssel'), None),
                (TextField(122000, 0, 88000, 15000, '(3) Lieferschein-Nr. (N)'), None),
                (TextField(0, 15000, 210000, 14000, '(8) Sach-Nr. Kunde (P)'), None),
                (TextField(0, 29000, 105000, 15000, '(9) Füllmenge (Q)'), None),
                (TextField(105000, 29000, 105000, 8000, '(10) Bezeichnung Lieferung, Leistung'), None),
                (TextField(105000, 37000, 105000, 14000, '(11) Sach-Nr. Lieferant (30S)'), None),
                (TextField(0, 44000, 105000, 15000, '(12) Lieferanten-Nr. (V)'), None),
                (TextField(105000, 51000, 40000, 8000, '(13) Datum'), None),
                (TextField(145000, 51000, 65000, 8000, '(14) Änderungsstand Konstruktion'), None),
                (TextField(0, 59000, 105000, 15000, '(15) Packstück-Nr. (S)'), None),
                (TextField(105000, 59000, 105000, 15000, '(16) Chargen-Nr. (H)'), None)
        ]

    def render(self, ctx, data):
        for field_obj, field_name in self.fields:
            ctx.save()
            try:
                field_obj.render(ctx)
                if field_name in data:
                    field_obj.render_data(ctx, data[field_name])
            finally:
                ctx.restore()

class GTLKLTLabel(object):
    fields = [
        BaseField(5_000, 2_000, 43_000 - 5_000, 21_500 - 2_000),
        BaseField(43_000, 2_000, 101_500 - 43_000, 21_500 - 2_000),
        BaseField(101_500, 2_000, 153_000 - 101_500, 21_500 - 2_000),
        BaseField(153_000, 2_000, 210_000 - 5_000 - 153_000, 21_500 - 2_000),
        BaseField(5_000, 21_500, 43_000 - 5_000, 34_000 - 21_500),
        BaseField(43_000, 21_500, 111_000 - 43_000, 34_000 - 21_500),
        BaseField(111_000, 21_500, 153_000 - 111_000, 34_000 - 21_500),
        BaseField(5_000, 34_000, 153_000 - 5_000, 46_000 - 34_000),
        BaseField(153_000, 21_500, 210_000 - 5_000 - 153_000, 46_000 - 21_500),
        BaseField(5_000, 46_000, 107_000 - 5_000, 74_000 - 5_000 - 46_000),
        BaseField(107_000, 46_000, 210_000 - 5_000 - 107_000, 74_000 - 5_000 - 46_000)
    ]

    def render(self, ctx, data=None):
        for field in self.fields:
            ctx.save()
            try:
                ctx.translate(field.position_x, field.position_y)
                field.render(ctx)
            finally:
                ctx.restore()

__all__ = ("KLTLabel", 'GTLKLTLabel')
