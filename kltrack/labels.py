import cairo
import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo

import enum

in_mm = lambda mms: mms / 25.4 * 72

def autosqueeze_layout(layout, field_width, normal_font, condensed_font):
    layout.set_font_description(normal_font)
    if layout.get_pixel_size()[0] >= field_width and condensed_font:
        layout.set_font_description(condensed_font)

class BaseField(object):
    position_x: float
    position_y: float
    width: float
    height: float
    label_text: str

    def __init__(self, position_x, position_y, width, height,
            label_text=None,
            show_borders=True,
            padding=(250, 250, 250, 250),
            label_position=(250, 250),
            label_font=None):
        if label_font is None:
            label_font = Pango.font_description_from_string(f"DejaVu Sans Condensed")
            label_font.set_absolute_size(2500 * Pango.SCALE)
        self.position_x = position_x
        self.position_y = position_y
        self.width = width
        self.height = height
        self.padding = padding
        self.label_position = label_position
        self.label_text = label_text
        self.label_font = label_font
        self.border_width = 100
        self.show_borders = show_borders

    @property
    def field_width(self):
        return self.width - self.padding_left - self.padding_right

    @property
    def field_height(self):
        return self.height - self.padding_top - self.padding_bottom

    @property
    def padding_left(self):
        return self.padding[3]
    
    @property
    def padding_right(self):
        return self.padding[1]

    @property
    def padding_top(self):
        return self.padding[0]

    @property
    def padding_bottom(self):
        return self.padding[2]

    def render_border(self, ctx):
        ctx.rectangle(0, 0, self.width, self.height)
        ctx.set_line_width(self.border_width)
        ctx.stroke()

    def render_label(self, ctx):
        layout = PangoCairo.create_layout(ctx)
        layout.set_font_description(self.label_font)
        layout.set_text(self.label_text)
        ctx.move_to(self.label_position[0], self.label_position[1])
        PangoCairo.show_layout(ctx, layout)

    def render_data(self, ctx, data):
        return NotImplemented

    def render(self, ctx):
        if self.show_borders:
            self.render_border(ctx)
        if self.label_text:
            self.render_label(ctx)

    def render_with_data(self, ctx, data):
        self.render(ctx)
        if data is not None:
            self.render_data(ctx, data)

class Alignment(enum.Enum):
    LEFT = enum.auto()
    TOP = LEFT
    CENTER = enum.auto()
    RIGHT = enum.auto()
    BOTTOM = RIGHT

    def to_pango_align(self):
        if self == Alignment.LEFT:
            return Pango.Alignment.LEFT
        elif self == Alignment.RIGHT:
            return Pango.Alignment.RIGHT
        elif self == Alignment.CENTER:
            return Pango.Alignment.CENTER

    def align_offset(self, outer_width, inner_width):
        if self == Alignment.LEFT:
            return 0
        elif self == Alignment.RIGHT:
            return outer_width - inner_width
        elif self == Alignment.CENTER:
            return (outer_width - inner_width)/2

class TextField(BaseField):
    def __init__(self, *args,
            data_font=None,
            long_data_font=None,
            alignment=Alignment.LEFT,
            vertical_alignment=Alignment.BOTTOM,
            only_uppercase=False,
            allow_markup=False,
            **kwargs):
        super().__init__(*args, **kwargs)
        if data_font is None:
            data_font = Pango.font_description_from_string(f"DejaVu Sans")
            data_font.set_absolute_size(5000 * Pango.SCALE)
        if long_data_font is None:
            long_data_font = Pango.font_description_from_string(f"DejaVu Sans Condensed")
            long_data_font.set_absolute_size(5000 * Pango.SCALE)
        self.alignment = alignment
        self.vertical_alignment = vertical_alignment
        self.data_font = data_font
        self.long_data_font = long_data_font
        self.only_uppercase = only_uppercase
        self.allow_markup = allow_markup

    def render_data(self, ctx, data):
        # Prepare Pango layout
        layout = PangoCairo.create_layout(ctx)
        if self.only_uppercase:
            data = data.upper()
        if self.allow_markup:
            layout.set_markup(data)
        else:
            layout.set_text(data)
        layout.set_font_description(self.data_font)
        font_size = self.data_font.get_size() / Pango.SCALE
        if self.field_width < layout.get_pixel_size()[0] and self.long_data_font:
            layout.set_font_description(self.long_data_font)
            font_size = self.long_data_font.get_size() / Pango.SCALE
        layout.set_width(self.field_width * Pango.SCALE)
        layout.set_height(self.field_height * Pango.SCALE)
        layout.set_alignment(self.alignment.to_pango_align())

        text_width, text_height = layout.get_pixel_size()
        if self.only_uppercase:
            text_height = font_size

        #pos_x = self.alignment.align_offset(self.field_width, text_width)
        pos_x = 0
        pos_y = self.vertical_alignment.align_offset(self.field_height, text_height)
        ctx.move_to(pos_x + self.padding_left, pos_y + self.padding_top)
        PangoCairo.show_layout(ctx, layout)

class SplitField(BaseField):
    def __init__(self, *args, sub_fields=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.sub_fields = sub_fields

    def render_label(self, ctx):
        if self.label_text:
            super().render_label(ctx)
        for sub_field in self.sub_fields:
            ctx.save()
            try:
                ctx.translate(sub_field.position_x, sub_field.position_y)
                sub_field.render_label(ctx)
            finally:
                ctx.restore()

    def render_data(self, ctx, data):
        for sub_field, field_data in zip(self.sub_fields, data):
            ctx.save()
            try:
                ctx.translate(sub_field.position_x, sub_field.position_y)
                sub_field.render_data(ctx, field_data)
            finally:
                ctx.restore()

    def render_border(self, ctx):
        super().render_border(ctx)
        for sub_field in self.sub_fields:
            ctx.save()
            try:
                ctx.translate(sub_field.position_x, sub_field.position_y)
                if sub_field.show_borders:
                    sub_field.render_border(ctx)
                ctx.move_to(sub_field.width, self.height)
                ctx.line_to(sub_field.width, self.height - 4000)
                ctx.set_line_width(self.border_width)
                ctx.stroke()
            finally:
                ctx.restore()

    def render(self, ctx):
        self.render_label(ctx)
        self.render_border(ctx)

class QRCodeField(BaseField):
    def __init__(self, *args, qr_parameters={"micro": False}, quiet_zone=4, **kwargs):
        self.qr_parameters = qr_parameters
        self.quiet_zone = quiet_zone
        super().__init__(*args, **kwargs)

    def render_data(self, ctx, data):
        # Generate QR Code
        import segno
        qr = segno.make(data, **self.qr_parameters)
        matrix = list(qr.matrix)
        del qr

        # Add quiet area
        quiet_data = [()] * self.quiet_zone
        matrix = quiet_data + [quiet_data + list(row) + quiet_data for row in matrix] + quiet_data

        qr_height, qr_width = len(matrix), max(len(row) for row in matrix)
        scale_factor = min(self.width / qr_width, self.height / qr_height)

        ctx.save()
        try:
            ctx.translate((self.width - qr_width * scale_factor)/2,
                    (self.height - qr_height * scale_factor)/2)
            ctx.scale(scale_factor, scale_factor)
            self._render_matrix(ctx, matrix)
        finally:
            ctx.restore()

    def render_label(self, ctx):
        pass

    def _render_matrix(self, ctx, matrix):
        for row in matrix:
            for col in row:
                if col:
                    ctx.rectangle(0, 0, 1, 1)
                    ctx.fill()
                ctx.translate(1, 0)
            ctx.translate(-len(row), 1)

class BarcodeField(TextField):
    codebook = {'1': ['1', '0', '0', '1', '0', '0', '0', '0', '1'], '2': ['0', '0', '1', '1', '0', '0', '0', '0', '1'], '3': ['1', '0', '1', '1', '0', '0', '0', '0', '0'], '4': ['0', '0', '0', '1', '1', '0', '0', '0', '1'], '5': ['1', '0', '0', '1', '1', '0', '0', '0', '0'], '6': ['0', '0', '1', '1', '1', '0', '0', '0', '0'], '7': ['0', '0', '0', '1', '0', '0', '1', '0', '1'], '8': ['1', '0', '0', '1', '0', '0', '1', '0', '0'], '9': ['0', '0', '1', '1', '0', '0', '1', '0', '0'], '0': ['0', '0', '0', '1', '1', '0', '1', '0', '0'], 'A': ['1', '0', '0', '0', '0', '1', '0', '0', '1'], 'B': ['0', '0', '1', '0', '0', '1', '0', '0', '1'], 'C': ['1', '0', '1', '0', '0', '1', '0', '0', '0'], 'D': ['0', '0', '0', '0', '1', '1', '0', '0', '1'], 'E': ['1', '0', '0', '0', '1', '1', '0', '0', '0'], 'F': ['0', '0', '1', '0', '1', '1', '0', '0', '0'], 'G': ['0', '0', '0', '0', '0', '1', '1', '0', '1'], 'H': ['1', '0', '0', '0', '0', '1', '1', '0', '0'], 'I': ['0', '0', '1', '0', '0', '1', '1', '0', '0'], 'J': ['0', '0', '0', '0', '1', '1', '1', '0', '0'], 'K': ['1', '0', '0', '0', '0', '0', '0', '1', '1'], 'L': ['0', '0', '1', '0', '0', '0', '0', '1', '1'], 'M': ['1', '0', '1', '0', '0', '0', '0', '1', '0'], 'N': ['0', '0', '0', '0', '1', '0', '0', '1', '1'], 'O': ['1', '0', '0', '0', '1', '0', '0', '1', '0'], 'P': ['0', '0', '1', '0', '1', '0', '0', '1', '0'], 'Q': ['0', '0', '0', '0', '0', '0', '1', '1', '1'], 'R': ['1', '0', '0', '0', '0', '0', '1', '1', '0'], 'S': ['0', '0', '1', '0', '0', '0', '1', '1', '0'], 'T': ['0', '0', '0', '0', '1', '0', '1', '1', '0'], 'U': ['1', '1', '0', '0', '0', '0', '0', '0', '1'], 'V': ['0', '1', '1', '0', '0', '0', '0', '0', '1'], 'W': ['1', '1', '1', '0', '0', '0', '0', '0', '0'], 'X': ['0', '1', '0', '0', '1', '0', '0', '0', '1'], 'Y': ['1', '1', '0', '0', '1', '0', '0', '0', '0'], 'Z': ['0', '1', '1', '0', '1', '0', '0', '0', '0'], '-': ['0', '1', '0', '0', '0', '0', '1', '0', '1'], '.': ['1', '1', '0', '0', '0', '0', '1', '0', '0'], ' ': ['0', '1', '1', '0', '0', '0', '1', '0', '0'], '*': ['0', '1', '0', '0', '1', '0', '1', '0', '0']}

    def __init__(self, *args, barcode_height=6000,
            barcode_spacing=250,
            barcode_alignment=Alignment.LEFT,
            show_text=True,
            **kwargs):
        if "padding" not in kwargs:
            kwargs["padding"] = (250, 250, 750, 6000)
        if "alignment" not in kwargs:
            kwargs["alignment"] = Alignment.RIGHT
        if "vertical_alignment" not in kwargs:
            kwargs["vertical_alignment"] = Alignment.TOP
        super().__init__(*args, **kwargs)
        self.barcode_height = barcode_height
        self.barcode_spacing = barcode_spacing
        self.barcode_alignment = barcode_alignment
        self.show_text = show_text

    def render_barcode(self, ctx, data):
        width = 0
        for char in "*" + data.upper() + "*":
            for pos, bar in enumerate(self.codebook[char]):
                bar_width = self.barcode_spacing * 3 if bar == "1" else self.barcode_spacing
                if pos % 2 == 0:
                    ctx.rectangle(0, 0, bar_width, self.barcode_height)
                    ctx.fill()
                ctx.translate(bar_width, 0)
                width += bar_width
            ctx.translate(self.barcode_spacing, 0)
            width += self.barcode_spacing
        return width

    def render_data(self, ctx, data):
        font_size = self.data_font.get_size() / Pango.SCALE

        # Calculate barcode width from barcode_spacing and len(data)
        barcode_width = self.barcode_spacing * (len(data) + 1) * 16

        pos_x = self.barcode_alignment.align_offset(self.field_width, barcode_width)
        pos_y = Alignment.BOTTOM.align_offset(self.field_height, self.barcode_height)

        # Render barcode with 6.4mm offset from left side at bottom
        ctx.save()
        try:
            ctx.translate(pos_x, pos_y)
            self.render_barcode(ctx, data)
        finally:
            ctx.restore()

        if self.show_text:
            TextField.render_data(self, ctx, data)

class ImageField(BaseField):
    def render_data(self, ctx, data):
        data = cairo.ImageSurface.create_from_png(data)
        padding = 1000
        wh_ratio = max(data.get_width() / (self.width - 2*padding), data.get_height() / (self.height - 2*padding))
        data.set_device_scale(wh_ratio, wh_ratio)
        old_source = ctx.get_source()
        ctx.save()
        try:
            ctx.translate(padding, (self.height - data.get_height() / wh_ratio) / 2)
            ctx.set_source_surface(data, 0, 0)
            ctx.paint()
        finally:
            ctx.restore()

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

class LagerLabel(object):
    width = 210000
    height = 74000

    def __init__(self):
        # Initialize font for grid labels
        self.grid_label_font = Pango.font_description_from_string("Fira Sans Condensed")
        self.grid_label_font.set_absolute_size(2500 * Pango.SCALE)
        # Initialize font for normal data
        self.normal_data_font = Pango.font_description_from_string("Fira Sans")
        self.normal_data_font.set_absolute_size(5000 * Pango.SCALE)
        # Initialize font for long data
        self.long_data_font = Pango.font_description_from_string("Fira Sans Compressed")
        self.long_data_font.set_absolute_size(5000 * Pango.SCALE)
        # Initialize font for large data
        self.large_data_font = Pango.font_description_from_string("Fira Sans")
        self.large_data_font.set_absolute_size(8000 * Pango.SCALE)
        # Initialize font for long large data
        self.large_long_data_font = Pango.font_description_from_string("Fira Sans Compressed")
        self.large_long_data_font.set_absolute_size(8000 * Pango.SCALE)

        font_settings = {
                "label_font": self.grid_label_font,
                "data_font": self.normal_data_font,
                "long_data_font": self.long_data_font
        }
        large_font_settings = {
                "label_font": self.grid_label_font,
                "data_font": self.large_data_font,
                "long_data_font": self.large_long_data_font
        }
        position_field = SplitField(40000, 0, 51000, 10000, sub_fields=(
            TextField(0, 0, 17000, 10000, '(1a) Loc',
                show_borders=False,
                alignment=Alignment.CENTER,
                only_uppercase=True,
                **large_font_settings),
            TextField(17000, 0, 17000, 10000, '(2) Rack',
                show_borders=False,
                alignment=Alignment.CENTER,
                only_uppercase=True,
                **large_font_settings),
            TextField(34000, 0, 17000, 10000, '(1c) Slot',
                show_borders=False,
                alignment=Alignment.CENTER,
                only_uppercase=True,
                **large_font_settings),
        ))
        policy_field = SplitField(40000, 64000, 130000, 10000, sub_fields=(
            TextField(0, 0, 25000, 10000, '(5) Richtlinie',
                show_borders=False,
                alignment=Alignment.CENTER,
                **font_settings),
            TextField(30000, 0, 50000, 10000, '(6) Verantwortung',
                show_borders=False,
                alignment=Alignment.LEFT,
                **font_settings)))
        self.fields = [
                #(BarcodeField(157000, 0, 53000, 10000, '(2) Behälter-Nr.', **large_font_settings), "id"),
                (position_field, 'pos'),
                (TextField(170000, 0, 40000, 10000, '(2) Behälter-Nr.',
                    alignment=Alignment.CENTER, only_uppercase=True, **large_font_settings), "id"),
                (BarcodeField(170000, 64000, 40000, 10000, '(2) Behälter-Nr.',
                    barcode_alignment=Alignment.RIGHT,
                    show_text=False), "id"),
                (ImageField(0, 0, 40000, 37000, '(3A) Logo', label_font=self.grid_label_font), "logo"),
                (TextField(0, 37000, 40000, 7000, '(3) Organisation', **font_settings,
                    padding=(250, 250, 0, 250), only_uppercase=True), "org"),
                (TextField(40000, 10000, 170000, 54000, '(4) Bezeichnung Inhalt',
                    allow_markup=True,
                    alignment=Alignment.CENTER,
                    vertical_alignment=Alignment.CENTER, **large_font_settings), "description"),
                (policy_field, "policy"),
                (QRCodeField(0, 44000, 40000, 30000, '(2) Behälter-Nr.', label_font=self.grid_label_font), "full_id"),
                #(TextField(40000, 44000, 170000, 30000, **font_settings), None)
        ]

    def render(self, ctx, data):
        for field_obj, field_name in self.fields:
            ctx.save()
            try:
                ctx.translate(field_obj.position_x, field_obj.position_y)
                field_obj.render(ctx)
                if field_name in data:
                    field_obj.render_data(ctx, data[field_name])
            finally:
                ctx.restore()

__all__ = ("LagerLabel", "in_mm")
