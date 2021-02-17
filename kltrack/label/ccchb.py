from .base import *

from gi.repository import Pango
import cairo

class KLTContainerLabel(object):
    width = 210_000
    height = 74_000

    def __init__(self, label_font=None, data_font=None, long_data_font=None,
            large_data_font=None, large_long_data_font=None,
            description_fonts=None):
        if description_fonts is None:
            basic_font = Pango.font_description_from_string("Fira Sans")
            description_fonts = []
            for font_size in (16_000, 14_000, 12_000, 10_000, 8_000):
                font = basic_font.copy()
                font.set_absolute_size(font_size * Pango.SCALE)
                description_fonts.append(font)
                del font
            del basic_font
        if label_font is None:
            label_font = Pango.font_description_from_string("Fira Sans Condensed")
            label_font.set_absolute_size(2_500 * Pango.SCALE)
        if data_font is None:
            data_font = Pango.font_description_from_string("Fira Sans")
            data_font.set_absolute_size(5_000 * Pango.SCALE)
            if long_data_font is None:
                long_data_font = Pango.font_description_from_string("Fira Sans Compressed")
                long_data_font.set_absolute_size(4_500 * Pango.SCALE)
        if large_data_font is None:
            large_data_font = Pango.font_description_from_string("Fira Sans")
            large_data_font.set_absolute_size(8_000 * Pango.SCALE)
            if large_long_data_font is None:
                large_long_data_font = Pango.font_description_from_string("Fira Sans Compressed")
                large_long_data_font.set_absolute_size(8_000 * Pango.SCALE)
        
        tnum_attrs = Pango.AttrList()
        tnum_attrs.insert(Pango.attr_font_features_new("tnum"))
        font_settings = {
                "label_font": label_font,
                "data_font": data_font,
                "long_data_font": long_data_font
        }
        large_font_settings = {
                "label_font": label_font,
                "data_font": large_data_font,
                "long_data_font": large_long_data_font
        }
        self._position_field = SplitField(35_000, 2_000, 130_000, 10_000, sub_fields=(
            TextField(0, 0, 17_000, 10_000, '(1a) Site',
                show_borders=False,
                alignment=Alignment.CENTER,
                only_uppercase=True,
                **large_font_settings),
            TextField(17_000, 0, 17_000, 10_000, '(1b) Rack',
                show_borders=False,
                alignment=Alignment.CENTER,
                only_uppercase=True,
                **large_font_settings),
            TextField(34_000, 0, 17_000, 10_000, '(1c) Slot',
                show_borders=False,
                alignment=Alignment.CENTER,
                only_uppercase=True,
                **large_font_settings),
        ))
        self._policy_field = SplitField(35_000, 59_000, 130_000, 10_000, sub_fields=(
            TextField(0, 0, 25_000, 10_000, '(5) Richtlinie',
                show_borders=False,
                alignment=Alignment.CENTER,
                **font_settings),
            TextField(30_000, 0, 50_000, 10_000, '(6) Verantwortung',
                show_borders=False,
                alignment=Alignment.LEFT,
                **font_settings)))
        self._id_field = TextField(165_000, 2_000, 40_000, 10_000, '(2) Behälter-Nr.',
            alignment=Alignment.CENTER, only_uppercase=True,
            text_attributes=tnum_attrs, **large_font_settings)
        self._id_barcode_field = BarcodeField(165_000, 59_000, 40_000, 10_000, '(2) Behälter-Nr.', label_font=label_font)
        self._url_field = QRCodeField(5_000, 39_000, 30_000, 30_000, label_font=label_font)
        self._description_field = TextField(35_000, 12_000, 170_000, 47_000, '(4) Bezeichnung Inhalt',
            allow_markup=True,
            alignment=Alignment.CENTER,
            vertical_alignment=Alignment.CENTER,
            data_fonts=description_fonts,
            label_font=label_font)
        self._org_field = TextField(5_000, 32_000, 30_000, 7_000, '(3) Organisation',
            padding=(250, 250, 0, 250),
            only_uppercase=True,
            **font_settings)
        self._logo_field = ImageField(5_000, 2_000, 30_000, 30_000,
            label_font=label_font)

    def render(self, ctx, data):
        fields = (
            (self._position_field, (data.get("pos_site"), data.get("pos_rack"), data.get("pos_slot"))),
            (self._policy_field, (data.get("policy"), data.get("responsible_person"))),
            (self._id_field, data.get("id")),
            (self._id_barcode_field, data.get("id")),
            (self._url_field, data.get("url")),
            (self._description_field, data.get("description")),
            (self._org_field, data.get("org")),
            (self._logo_field, data.get("org_logo"))
        )
        for field, field_data in fields:
            ctx.save()
            try:
                ctx.translate(field.position_x, field.position_y)
                field.render(ctx)
                if field_data is not None:
                    field.render_data(ctx, field_data)
            finally:
                ctx.restore()

class QRCodeLabel(object):
    def __init__(self, width, height, data_fonts=None, font_family="Fira Sans"):
        self.width = width
        self.height = height

        if data_fonts is None:
            data_fonts = []
            base_data_font = Pango.font_description_from_string(font_family)
            for size in range(3, 10):
                data_font = base_data_font.copy()
                data_font.set_absolute_size(self.height / size * Pango.SCALE)
                data_fonts.append(data_font)
        
        id_fonts = []
        for data_font in data_fonts:
            id_font = data_font.copy()
            id_font.set_weight(Pango.Weight.BOLD)
            id_fonts.append(id_font)

        self._qrcode_field = QRCodeField(0, 0, self.height, self.height,
                quiet_zone=0,
                qr_parameters={},
                padding=(3_000, 250, 3_000, 3_000))
        self._id_field = TextField(self.height, 0, self.width - self.height,
                self.height // 2,
                allow_markup=True,
                data_fonts=id_fonts,
                alignment=Alignment.CENTER,
                vertical_alignment=Alignment.BOTTOM,
                padding=(3_000, 3_000, 250, 250))
        self._description_field = TextField(self.height, self.height // 2,
                self.width - self.height, self.height // 2,
                data_fonts=data_fonts,
                padding=(250, 3_000, 3_000, 250),
                alignment=Alignment.CENTER,
                vertical_alignment=Alignment.TOP)
    
    def render(self, ctx, data):
        fields = (
                (self._qrcode_field, data.get("url") or data.get("full_id") or data.get("id")),
                (self._id_field, data.get("id")),
                (self._description_field, data.get("description"))
        )
        for field, field_data in fields:
            ctx.save()
            try:
                ctx.translate(field.position_x, field.position_y)
                if field_data is not None:
                    field.render_data(ctx, field_data)
            finally:
                ctx.restore()

class BarcodeLabel(object):
    def __init__(self, width, height, barcode_height=6_000, data_font=None, font_family="Fira Sans"):
        self.width = width
        self.height = height

        if data_font is None:
            data_font = Pango.font_description_from_string(font_family)
            data_font.set_absolute_size(6_000 * Pango.SCALE)
        
        actual_height = height - 2 * 3_000 - barcode_height


        self._barcode_field = BarcodeField(0, height - 3_250 - barcode_height, width, barcode_height + 2 * 250,
            alignment=Alignment.CENTER,
            vertical_alignment=Alignment.TOP,
            padding=(250, 0, 0, 0))

        self._id_field = TextField(0, height - 3_250 - barcode_height - 6_000 - 250, width, 6_000 + 250,
            alignment=Alignment.CENTER,
            vertical_alignment=Alignment.BOTTOM,
            padding=(250, 3_000, 0, 3_000))
        self._description_field = None
        if height >= 24_000:
            self._description_field = TextField(0, 0, width, height - 3_000 - 2 * 250 - barcode_height - 6_000,
                alignment=Alignment.CENTER,
                vertical_alignment=Alignment.CENTER,
                padding=(3_000, 3_000, 0, 3_000))

    def render(self, ctx, data):
        fields = [
            (self._barcode_field, data.get("id")),
            (self._id_field, data.get("full_id") or data.get("id"))
        ]
        if self._description_field:
            fields.append((self._description_field, data.get("description")))
        for field, field_data in fields:
            ctx.save()
            try:
                ctx.translate(field.position_x, field.position_y)
                if field_data is not None:
                    field.render_data(ctx, field_data)
            finally:
                ctx.restore()

__all__ = ("KLTContainerLabel", "QRCodeLabel", "BarcodeLabel")
