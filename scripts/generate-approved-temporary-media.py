from pathlib import Path
from PIL import Image, ImageOps
import hashlib, json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "imges/destinations/temporary"
OUT = ROOT / "imges/optimized/destinations"
FAMILIES = {
    "awjila-master": ("awjila-master.jpg", [640, 1280, 1600], 88),
    "awjila-gallery-01": ("awjila-gallery-01.jpg", [960], 86),
    "awjila-gallery-02": ("awjila-gallery-02.jpg", [960], 86),
    "awjila-gallery-03": ("awjila-gallery-03.jpg", [960], 86),
    "awjila-gallery-04": ("awjila-gallery-04.jpg", [960], 86),
    "nafusa": ("nafusa-mountains.jpg", [640, 1280, 1600], 88),
    "bomba-bay": ("bomba-bay.png", [640, 1042], 88),
    "villa-sileen-columns": ("villa-sileen-columns.jpg", [960, 1600], 88),
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def encode(source, output, width, quality):
    with Image.open(source) as raw:
        icc = raw.info.get("icc_profile")
        image = ImageOps.exif_transpose(raw).convert("RGB")
        if width > image.width:
            raise ValueError(f"Refusing to upscale {source}")
        height = round(image.height * width / image.width)
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        options = {"format": "WEBP", "quality": quality, "method": 6}
        if icc:
            options["icc_profile"] = icc
        image.save(output, **options)
        return width, height

results = []
OUT.mkdir(parents=True, exist_ok=True)
for family, (filename, widths, quality) in FAMILIES.items():
    source = SRC / filename
    for width in widths:
        output = OUT / f"{family}-{width}.webp"
        dimensions = encode(source, output, width, quality)
        repeat = OUT / f".{family}-{width}-repeat.webp"
        encode(source, repeat, width, quality)
        deterministic = sha(output) == sha(repeat)
        repeat.unlink()
        signature = output.read_bytes()[:12]
        with Image.open(output) as decoded:
            decoded.load()
            actual = decoded.size
        if signature[:4] != b"RIFF" or signature[8:12] != b"WEBP":
            raise ValueError(f"Invalid WebP signature: {output}")
        if actual != dimensions or output.stat().st_size >= source.stat().st_size or not deterministic:
            raise ValueError(f"Derivative validation failed: {output}")
        results.append({
            "path": output.relative_to(ROOT).as_posix(),
            "source": source.relative_to(ROOT).as_posix(),
            "width": dimensions[0],
            "height": dimensions[1],
            "quality": quality,
            "bytes": output.stat().st_size,
            "sha256": sha(output),
            "deterministic": deterministic,
        })

print(json.dumps(results, indent=2))
