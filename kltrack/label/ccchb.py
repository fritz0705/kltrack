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

class ExtendedInventoryLabel(object):
    width = 90_000
    height = 38_000

    def __init__(self):
        text_font = Pango.font_description_from_string("Fira Sans")
        text_font.set_absolute_size(9_000 * Pango.SCALE)

        self._id_qr_field = QRCodeField(2_000, 2_000, 34_000, 34_000,
            quiet_zone=3, qr_parameters={"micro": True})
        self._id_field = TextField(38_000, 26_000, 50_000, 10_000,
            data_font=text_font,
            vertical_alignment=Alignment.CENTER)
        self._description_field = TextField(38_000, 2_000, 50_000, 22_000,
            data_font=text_font,
            vertical_alignment=Alignment.CENTER)
    
    def render(self, ctx, data):
        fields = (
            (self._id_qr_field, data.get("id")),
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


class Inventory62x29Label(object):
    width = 62_000
    height = 29_000

    def __init__(self, data_font=None):
        if data_font is None:
            data_font = Pango.font_description_from_string("Fira Sans")
            data_font.set_absolute_size(9_000 * Pango.SCALE)

        self._qrcode_field = QRCodeField(0, 0, 29_000, 29_000,
                quiet_zone=5)
        self._id_field = TextField(29_000, 2_000, 31_000, 25_000,
                vertical_alignment=Alignment.CENTER,
                alignment=Alignment.CENTER,
                data_fonts=[data_font,])

    def render(self, ctx, data):
        fields = (
            (self._qrcode_field, data.get("url")),
            (self._id_field, data.get("id")),
        )
        for field, field_data in fields:
            ctx.save()
            try:
                ctx.translate(field.position_x, field.position_y)
                if field_data is not None:
                    field.render_data(ctx, field_data)
            finally:
                ctx.restore()

class QRCodeLabel(object):
    def __init__(self, width, height, data_fonts=None):
        self.width = width
        self.height = height

        if data_fonts is None:
            data_fonts = []
            base_data_font = Pango.font_description_from_string("Fira Sans")
            for size in range(3, 10):
                data_font = base_data_font.copy()
                data_font.set_absolute_size(self.height / size * Pango.SCALE)
                data_fonts.append(data_font)

        self._qrcode_field = QRCodeField(0, 0, self.height, self.height,
                quiet_zone=0,
                padding=(3_000, 250, 3_000, 3_000))
        self._id_field = TextField(self.height, 0, self.width - self.height,
                self.height // 2,
                data_fonts=data_fonts,
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
                (self._id_field, data.get("full_id") or data.get("id")),
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
    def __init__(self, width, height, data_font=None):
        self.width = width
        self.height = height

        if data_font is None:
            data_font = Pango.font_description_from_string("Fira Sans")
            data_font.set_absolute_size(max(self.height // 4, 6_000) * Pango.SCALE)
        
        self._barcode_field = BarcodeField(0, self.height / 2, self.width, self.height / 2,
                barcode_height=min(6_000, self.height / 2),
                vertical_alignment=Alignment.TOP)
        self._id_field = TextField(0, 0, self.width, self.height / 2,
                alignment=Alignment.CENTER,
                vertical_alignment=Alignment.BOTTOM,
                data_fonts=[data_font])

    def render(self, ctx, data):
        fields = (
            (self._barcode_field, data.get("id")),
            (self._id_field, data.get("full_id") or data.get("id"))
        )
        for field, field_data in fields:
            ctx.save()
            try:
                ctx.translate(field.position_x, field.position_y)
                if field_data is not None:
                    field.render_data(ctx, field_data)
            finally:
                ctx.restore()

if __name__ == "__main__":
    import argparse

    label_types = {
        "klt_container": KLTContainerLabel,
        "klt": KLTContainerLabel,
        "barcode-62x29": lambda: BarcodeLabel(62_000, 29_000),
        "barcode-90x38": lambda: BarcodeLabel(90_000, 38_000),
        "barcode-54x17": lambda: BarcodeLabel(54_000, 17_000),
        "qr-62x29": lambda: QRCodeLabel(62_000, 29_000),
        "qr-54x17": lambda: QRCodeLabel(54_000, 17_000),
        "qr-90x38": lambda: QRCodeLabel(90_000, 38_000),
        "extended_inventory": ExtendedInventoryLabel,
        "extended": ExtendedInventoryLabel,
    }

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--size", "-s", default="raw", choices=("a4", "a5", "raw"))
    argparser.add_argument("--field", "-f", nargs=2, action="append")
    argparser.add_argument("--output-format", default="pdf", choices=("pdf", "svg"))
    argparser.add_argument("--output-file", default="out.pdf")
    argparser.add_argument("--json")
    argparser.add_argument("label_type", choices=tuple(label_types))
    args = argparser.parse_args()

    label = label_types[args.label_type]()

    if args.size == "raw":
        surface_width, surface_height = label.width, label.height
    elif args.size == "a4":
        surface_width, surface_height = 210_000, 296_000
    elif args.size == "a5":
        surface_width, surface_height = 210_000, 148_000
    
    if args.output_format == "pdf":
        surface = cairo.PDFSurface(args.output_file, surface_width * 720 / (254 * 1_000), surface_height * 720 / (254 * 1_000))
    elif args.output_format == "svg":
        surface = cairo.SVGSurface(args.output_file, surface_width * 720 / (254 * 1_000), surface_height * 720 / (254 * 1_000))

    ctx = cairo.Context(surface)
    if args.output_format in {"svg", "pdf"}:
        ctx.scale(720 / (254 * 1_000), 720 / (254 * 1_000))
    
    if args.size == "a4":
        ctx.translate(0, 148_000)
    elif args.size == "a5":
        ctx.translate(0, 3_000)

    json_data = {}
    if args.json:
        import json, sys
        json_file = sys.stdin if args.json == "-" else open(args.json)
        json_data = json.load(json_file)
    args_data = dict(args.field or ())

    if isinstance(json_data, list):
        for entry in json_data:
            entry.update(args_data)
            label.render(ctx, entry)
            ctx.show_page()
    else:
        json_data.update(args_data)
        label.render(ctx, json_data)

    surface.finish()

__all__ = ("KLTContainerLabel", "BasicInventoryLabel",)
