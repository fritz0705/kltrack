import cairo
import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo

import enum

# The basic unit of measurement in this module are millimeters.

in_mm = lambda mms: mms * 720 / 254

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
            label_font.set_absolute_size(2_500 * Pango.SCALE)
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
            data_fonts=None,
            data_font=None,
            long_data_font=None,
            alignment=Alignment.LEFT,
            vertical_alignment=Alignment.BOTTOM,
            only_uppercase=False,
            allow_markup=False,
            text_attributes=None,
            **kwargs):
        super().__init__(*args, **kwargs)
        if data_font is None:
            data_font = Pango.font_description_from_string(f"DejaVu Sans")
            data_font.set_absolute_size(5_000 * Pango.SCALE)
        if long_data_font is None:
            long_data_font = Pango.font_description_from_string(f"DejaVu Sans Condensed")
            long_data_font.set_absolute_size(5_000 * Pango.SCALE)
        if data_fonts is None:
            data_fonts = [data_font, long_data_font]
        self.alignment = alignment
        self.vertical_alignment = vertical_alignment
        self.data_fonts = data_fonts
        self.only_uppercase = only_uppercase
        self.allow_markup = allow_markup
        self.text_attributes = text_attributes

    def render_data(self, ctx, data):
        if not data:
            return

        # Prepare Pango layout
        layout = PangoCairo.create_layout(ctx)
        if self.only_uppercase:
            data = data.upper()
        if self.allow_markup:
            layout.set_markup(data)
        else:
            layout.set_text(data)
        if self.text_attributes is not None:
            layout.set_attributes(self.text_attributes)
        for font in self.data_fonts:
            font_size = font.get_size() / Pango.SCALE
            layout.set_font_description(font)
            if self.field_width >= layout.get_pixel_size()[0]:
                break

        # Apply field width and height for Pango layout engine
        layout.set_width(self.field_width * Pango.SCALE)
        layout.set_height(self.field_height * Pango.SCALE)

        # Ensure proper alignment
        layout.set_alignment(self.alignment.to_pango_align())

        text_width, text_height = layout.get_pixel_size()
        if self.only_uppercase:
            text_height = font_size

        # This is, actually, not neccessary, since Pango handles this for us.
        #pos_x = self.alignment.align_offset(self.field_width, text_width)
        pos_x = 0
        pos_y = self.vertical_alignment.align_offset(self.field_height, text_height)

        # Render the actual text
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
                ctx.line_to(sub_field.width, self.height - 4_000)
                ctx.set_line_width(self.border_width)
                ctx.stroke()
            finally:
                ctx.restore()

    def render(self, ctx):
        self.render_label(ctx)
        self.render_border(ctx)

class QRCodeField(BaseField):
    def __init__(self, *args, qr_parameters={"micro": False, "error": "Q"}, quiet_zone=8, **kwargs):
        self.qr_parameters = qr_parameters
        self.quiet_zone = quiet_zone
        super().__init__(*args, **kwargs)

    def render_data(self, ctx, data):
        # Generate QR Code
        import segno
        qr = segno.make(data, **self.qr_parameters)
        matrix = list(qr.matrix)
        del qr

        # Add quiet zone
        quiet_data = [()] * self.quiet_zone
        matrix = quiet_data + [quiet_data + list(row) + quiet_data for row in matrix] + quiet_data

        qr_height, qr_width = len(matrix), max(len(row) for row in matrix)
        scale_factor = min(self.width / qr_width, self.height / qr_height)

        ctx.save()
        try:
            ctx.translate(Alignment.CENTER.align_offset(self.field_width, qr_width * scale_factor) + self.padding_left,
                    Alignment.CENTER.align_offset(self.field_height, qr_height * scale_factor + self.padding_top))
            ctx.scale(scale_factor, scale_factor)
            self._render_matrix(ctx, matrix)
        finally:
            ctx.restore()

    def render_label(self, ctx):
        # No label for QR codes
        pass

    def _render_matrix(self, ctx, matrix):
        for row in matrix:
            for col in row:
                if col:
                    ctx.rectangle(0, 0, 1, 1)
                    ctx.fill()
                ctx.translate(1, 0)
            ctx.translate(-len(row), 1)

class BarcodeField(BaseField):
    codebook = {'1': ['1', '0', '0', '1', '0', '0', '0', '0', '1'], '2': ['0', '0', '1', '1', '0', '0', '0', '0', '1'], '3': ['1', '0', '1', '1', '0', '0', '0', '0', '0'], '4': ['0', '0', '0', '1', '1', '0', '0', '0', '1'], '5': ['1', '0', '0', '1', '1', '0', '0', '0', '0'], '6': ['0', '0', '1', '1', '1', '0', '0', '0', '0'], '7': ['0', '0', '0', '1', '0', '0', '1', '0', '1'], '8': ['1', '0', '0', '1', '0', '0', '1', '0', '0'], '9': ['0', '0', '1', '1', '0', '0', '1', '0', '0'], '0': ['0', '0', '0', '1', '1', '0', '1', '0', '0'], 'A': ['1', '0', '0', '0', '0', '1', '0', '0', '1'], 'B': ['0', '0', '1', '0', '0', '1', '0', '0', '1'], 'C': ['1', '0', '1', '0', '0', '1', '0', '0', '0'], 'D': ['0', '0', '0', '0', '1', '1', '0', '0', '1'], 'E': ['1', '0', '0', '0', '1', '1', '0', '0', '0'], 'F': ['0', '0', '1', '0', '1', '1', '0', '0', '0'], 'G': ['0', '0', '0', '0', '0', '1', '1', '0', '1'], 'H': ['1', '0', '0', '0', '0', '1', '1', '0', '0'], 'I': ['0', '0', '1', '0', '0', '1', '1', '0', '0'], 'J': ['0', '0', '0', '0', '1', '1', '1', '0', '0'], 'K': ['1', '0', '0', '0', '0', '0', '0', '1', '1'], 'L': ['0', '0', '1', '0', '0', '0', '0', '1', '1'], 'M': ['1', '0', '1', '0', '0', '0', '0', '1', '0'], 'N': ['0', '0', '0', '0', '1', '0', '0', '1', '1'], 'O': ['1', '0', '0', '0', '1', '0', '0', '1', '0'], 'P': ['0', '0', '1', '0', '1', '0', '0', '1', '0'], 'Q': ['0', '0', '0', '0', '0', '0', '1', '1', '1'], 'R': ['1', '0', '0', '0', '0', '0', '1', '1', '0'], 'S': ['0', '0', '1', '0', '0', '0', '1', '1', '0'], 'T': ['0', '0', '0', '0', '1', '0', '1', '1', '0'], 'U': ['1', '1', '0', '0', '0', '0', '0', '0', '1'], 'V': ['0', '1', '1', '0', '0', '0', '0', '0', '1'], 'W': ['1', '1', '1', '0', '0', '0', '0', '0', '0'], 'X': ['0', '1', '0', '0', '1', '0', '0', '0', '1'], 'Y': ['1', '1', '0', '0', '1', '0', '0', '0', '0'], 'Z': ['0', '1', '1', '0', '1', '0', '0', '0', '0'], '-': ['0', '1', '0', '0', '0', '0', '1', '0', '1'], '.': ['1', '1', '0', '0', '0', '0', '1', '0', '0'], ' ': ['0', '1', '1', '0', '0', '0', '1', '0', '0'], '*': ['0', '1', '0', '0', '1', '0', '1', '0', '0']}

    def __init__(self, *args, barcode_height=6_000,
            barcode_spacing=250,
            alignment=Alignment.CENTER,
            vertical_alignment=Alignment.BOTTOM,
            padding=(250, 750, 750, 750),
            **kwargs):
        super().__init__(*args,
                padding=padding,
                **kwargs)
        self.alignment = alignment
        self.vertical_alignment = vertical_alignment
        self.barcode_height = barcode_height
        self.barcode_spacing = barcode_spacing

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

    def barcode_width(self, data):
        return ((len(data) + 2) * 16 - 1) * self.barcode_spacing

    def render_data(self, ctx, data):
        # Calculate barcode width from barcode_spacing and len(data)
        barcode_width = self.barcode_width(data)

        pos_x = self.alignment.align_offset(self.field_width, barcode_width)
        pos_y = self.vertical_alignment.align_offset(self.field_height, self.barcode_height)

        ctx.save()
        try:
            ctx.translate(pos_x + self.padding_left, pos_y + self.padding_top)
            self.render_barcode(ctx, data)
        finally:
            ctx.restore()

class ImageField(BaseField):
    def __init__(self, *args, alignment=Alignment.CENTER,
            vertical_alignment=Alignment.CENTER,
            **kwargs):
        super().__init__(*args,
                **kwargs)
        self.alignment = alignment
        self.vertical_alignment = vertical_alignment

    def render_data(self, ctx, data):
        # TODO Refactor wtf
        data = cairo.ImageSurface.create_from_png(data)
        padding = 1_000
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

__all__ = ("BaseField", "TextField", "QRCodeField", "BarcodeField",
        "ImageField", "SplitField", "in_mm", "Alignment")
