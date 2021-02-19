import argparse

import cairo

from .ccchb import *
from .vda import *

label_types = {
    "container-klt": KLTContainerLabel,
    "barcode-62x29": lambda: BarcodeLabel(62_000, 29_000),
    "barcode-90x38": lambda: BarcodeLabel(90_000, 38_000),
    "barcode-54x17": lambda: BarcodeLabel(54_000, 17_000),
    "qr-62x29": lambda: QRCodeLabel(62_000, 29_000),
    "qr-54x17": lambda: QRCodeLabel(54_000, 17_000),
    "qr-90x38": lambda: QRCodeLabel(90_000, 38_000),
    "dmtx-54x17": lambda: DataMatrixLabel(54_000, 17_000),
    "klt": KLTLabel,
    "gtl-klt": GTLKLTLabel
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