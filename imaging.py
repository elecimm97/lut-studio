"""Image validation, original color presets and trilinear .cube processing."""
from io import BytesIO
import warnings
import numpy as np
from PIL import Image, ImageOps, ImageCms, UnidentifiedImageError

MAX_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 16_000_000
PRESETS = {'original': 'Original', 'amber': 'Amber · warm', 'ocean': 'Ocean · cool', 'mono': 'Mono · black & white', 'fade': 'Fade · soft', 'custom': 'Custom LUT (.cube)'}


def load_image(path):
    """Decode one still PNG/JPEG/WebP and normalize orientation and color to sRGB."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(path) as src:
                if src.format not in {'PNG', 'JPEG', 'WEBP'}:
                    raise ValueError('Use a PNG, JPEG or WebP file.')
                if src.width * src.height > MAX_PIXELS:
                    raise ValueError('Image too large: maximum 16 megapixels.')
                if getattr(src, 'n_frames', 1) != 1:
                    raise ValueError('Only still images are supported.')
                img = ImageOps.exif_transpose(src).convert('RGBA')
                profile = src.info.get('icc_profile')
                if profile:
                    rgb = ImageCms.profileToProfile(img.convert('RGB'), ImageCms.ImageCmsProfile(BytesIO(profile)), ImageCms.createProfile('sRGB'), outputMode='RGB')
                    rgb.putalpha(img.getchannel('A'))
                    img = rgb
                return img
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning, ImageCms.PyCMSError) as exc:
        raise ValueError('Unreadable image or invalid color profile. Try another file.') from exc


def read_cube(text):
    """Read 3D .cube files; red is the fastest-changing channel in the file."""
    size, rows = None, []
    lo, hi = np.zeros(3, dtype=np.float32), np.ones(3, dtype=np.float32)
    seen = set()
    for line in text.splitlines():
        parts = line.split('#', 1)[0].strip().split()
        if not parts:
            continue
        key = parts[0]
        if key == 'TITLE':
            continue
        if key in {'LUT_3D_SIZE', 'DOMAIN_MIN', 'DOMAIN_MAX'}:
            if key in seen:
                raise ValueError('Duplicate LUT header.')
            seen.add(key)
            if key == 'LUT_3D_SIZE':
                if len(parts) != 2:
                    raise ValueError('Invalid LUT size.')
                size = int(parts[1])
                if not 2 <= size <= 65:
                    raise ValueError('LUT size must be between 2 and 65.')
            else:
                values = np.array(parts[1:], dtype=np.float32)
                if values.shape != (3,):
                    raise ValueError('Invalid LUT domain.')
                if key == 'DOMAIN_MIN': lo = values
                else: hi = values
        else:
            if len(parts) != 3:
                raise ValueError('Only 3D .cube LUTs without 1D shapers are supported.')
            rows.append([float(x) for x in parts])
            if len(rows) > 65 ** 3:
                raise ValueError('LUT too large.')
    if size is None or len(rows) != size ** 3:
        raise ValueError('Row count does not match LUT_3D_SIZE.')
    table = np.array(rows, dtype=np.float32).reshape(size, size, size, 3)
    if not all(np.isfinite(a).all() for a in (table, lo, hi)) or np.any(hi <= lo):
        raise ValueError('The LUT contains invalid values or domain.')
    return table, lo, hi


def transform(rgb, preset, cube=None):
    if preset == 'original': return rgb
    if preset == 'custom':
        if cube is None: raise ValueError('Upload a .cube LUT to use this look.')
        table, lo, hi = cube
        coords = np.clip((rgb - lo) / (hi - lo), 0, 1) * (len(table) - 1)
        a = np.floor(coords).astype(np.int32)
        b = np.minimum(a + 1, len(table) - 1)
        f = coords - a
        result = np.zeros_like(rgb)
        for r in (0, 1):
            for g in (0, 1):
                for blue in (0, 1):
                    ri, gi, bi = (b[..., 0] if r else a[..., 0], b[..., 1] if g else a[..., 1], b[..., 2] if blue else a[..., 2])
                    w = (f[..., 0] if r else 1-f[..., 0]) * (f[..., 1] if g else 1-f[..., 1]) * (f[..., 2] if blue else 1-f[..., 2])
                    result += table[bi, gi, ri] * w[..., None]
        return np.clip(result, 0, 1)
    if preset == 'amber': return np.clip(rgb * [1.08, 1.00, .90] + [.025, .005, 0], 0, 1)
    if preset == 'ocean': return np.clip(rgb * [.91, 1.02, 1.09] + [0, .008, .018], 0, 1)
    if preset == 'mono': return np.repeat((rgb @ np.array([.2126, .7152, .0722]))[..., None], 3, axis=-1)
    if preset == 'fade': return np.clip(rgb * .80 + .11, 0, 1)
    raise ValueError('Unknown look.')


def apply_filter(image, preset, intensity, cube=None):
    """Process in row chunks to keep full-resolution export memory bounded."""
    if not 0 <= intensity <= 100: raise ValueError('Invalid intensity.')
    out = image.convert('RGBA').copy()
    if intensity == 0 or preset == 'original': return out
    for y in range(0, image.height, 128):
        block = np.array(out.crop((0, y, image.width, min(y+128, image.height))))
        rgb = block[..., :3].astype(np.float32) / 255
        changed = transform(rgb, preset, cube)
        block[..., :3] = np.rint(np.clip(rgb + (changed-rgb) * (intensity/100), 0, 1) * 255).astype(np.uint8)
        out.paste(Image.fromarray(block), (0, y))
    return out


def png_bytes(image):
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()
