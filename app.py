"""LUT Studio — session-isolated reactive photo editor."""
import base64
import re
from functools import lru_cache
from pathlib import Path
from shiny import App, reactive, render, ui, req
from imaging import PRESETS, MAX_BYTES, load_image, read_cube, apply_filter, png_bytes

ROOT = Path(__file__).parent
# Replace None with your published website URL, e.g. "https://your-site.example".
CREATOR_URL = "https://elecimm97.github.io/ElenaCimmino.github.io/"
CREATOR_NAME = "Elena Cimmino"
creator_credit = ui.div(
    'Created by ',
    ui.tags.a(CREATOR_NAME, href=CREATOR_URL, target='_blank', rel='noopener noreferrer')
    if CREATOR_URL else ui.tags.span(CREATOR_NAME),
    ' · ',
    ui.tags.a('View my CV', href=CREATOR_URL, target='_blank', rel='noopener noreferrer')
    if CREATOR_URL else ui.tags.span('Website coming soon'),
    class_='creator',
)
LUT_FILES = {f"lut:{p.name}": p for p in sorted((ROOT / 'luts').glob('*.cube'), key=lambda p: int(re.search(r'\d+', p.stem).group()) if re.search(r'\d+', p.stem) else 0)}
LOOKS = {**{k: v for k, v in PRESETS.items() if k != 'custom'}, **{k: p.stem.replace('_', ' ') for k, p in LUT_FILES.items()}, 'custom': PRESETS['custom']}

@lru_cache(maxsize=64)
def bundled_lut(key):
    return read_cube(LUT_FILES[key].read_text(encoding='utf-8-sig'))

app_ui = ui.page_fluid(
    ui.tags.head(ui.tags.style((ROOT / 'style.css').read_text()), ui.tags.script((ROOT / 'theme.js').read_text())),
    ui.div(ui.tags.button('Dark mode', id='theme-toggle', type='button', **{'aria-pressed': 'false', 'aria-label': 'Switch to dark mode'}), class_='theme-toolbar'),
    ui.div(ui.span('LUT STUDIO', class_='eyebrow'), ui.h1('Give your photos a new mood.'),
           ui.p('Find your photo’s next mood.', class_='subtitle'), class_='hero'),
    ui.div(
        ui.div(ui.h2('Your studio'),
            ui.input_file('photo', '01 / Upload a photo', accept=['.png', '.jpg', '.jpeg', '.webp'], button_label='Browse', placeholder='PNG, JPEG or WebP'),
            ui.input_action_button('demo', 'Try a sample'),
            ui.p('Max 20 MB · 16 megapixels · still images', class_='hint'),
            ui.input_select('preset', '02 / Choose your look', choices=LOOKS, selected=next(iter(LUT_FILES), 'amber')),
            ui.panel_conditional("input.preset === 'custom'", ui.input_file('cube', 'LUT 3D (.cube)', accept=['.cube']), ui.p('Size 2–65. Use LUTs designed for sRGB images.', class_='hint')),
            ui.input_slider('intensity', '03 / Intensity', min=0, max=100, value=70, post='%'),
            ui.input_action_button('reset', 'Reset to original', class_='reset'),
            ui.output_ui('save'),
            ui.p('Preview updates automatically. Downloads keep the original resolution.', class_='hint'), class_='controls'),
        ui.div(ui.output_ui('status'), ui.div(ui.div(ui.h2('Original'), ui.output_ui('before'), class_='photo-card'), ui.div(ui.h2('Your look'), ui.output_ui('after'), class_='photo-card'), class_='comparison'), class_='stage'), class_='workspace'),
    ui.div(creator_credit, ui.p('Built with Python + Shiny · Color presets and custom 3D LUTs'), class_='footer'),
    title='LUT Studio',
)


def server(input, output, session):
    selected = reactive.Value(None)

    @reactive.effect
    @reactive.event(input.photo)
    def uploaded():
        files = input.photo()
        if files:
            selected.set(files[0])

    @reactive.effect
    @reactive.event(input.demo)
    def demo():
        path = ROOT / 'docs' / 'sample.png'
        selected.set({'datapath': str(path), 'size': path.stat().st_size})

    @reactive.calc
    def source():
        file = selected.get()
        if file is None: return None, None
        files = [file]
        try:
            if files[0]['size'] > MAX_BYTES: raise ValueError('File too large: maximum 20 MB.')
            return load_image(files[0]['datapath']), None
        except ValueError as exc: return None, str(exc)

    @reactive.calc
    def lut():
        if input.preset() in LUT_FILES:
            try:
                return bundled_lut(input.preset()), None
            except (ValueError, OSError):
                return None, 'Could not read this LUT. Choose another look.'
        if input.preset() != 'custom': return None, None
        files = input.cube()
        if not files: return None, 'Upload a .cube LUT to see your result.'
        try:
            if files[0]['size'] > 12 * 1024 * 1024: raise ValueError('LUT too large: maximum 12 MB.')
            return read_cube(Path(files[0]['datapath']).read_text(encoding='utf-8-sig')), None
        except (ValueError, OSError) as exc:
            return None, 'Invalid LUT. ' + (str(exc) if isinstance(exc, ValueError) else 'Could not read the file.')

    @reactive.calc
    def preview():
        img, error = source()
        if img is None: return None
        img = img.copy()
        img.thumbnail((1200, 1200))
        return img

    @reactive.effect
    @reactive.event(input.reset)
    def reset():
        ui.update_select('preset', selected='original')
        ui.update_slider('intensity', value=0)

    def photo_tag(img):
        encoded = base64.b64encode(png_bytes(img)).decode('ascii')
        return ui.tags.img(src='data:image/png;base64,' + encoded, alt='Image preview', class_='preview')

    @render.ui
    def status():
        img, error = source()
        _, lut_error = lut()
        if error or (img is not None and lut_error): return ui.div(error or lut_error, role='alert', class_='notice error')
        if img is None: return ui.div('Upload a photo or try a sample to explore your next look.', class_='notice')
        return ui.div(f'{img.width} × {img.height} px · {LOOKS[input.preset()]} · Intensity {input.intensity()}%', class_='notice', role='status')

    @render.ui
    def before():
        img = preview()
        return photo_tag(img) if img is not None else ui.div('Your original photo', class_='empty')

    @render.ui
    def after():
        img = preview()
        cube, error = lut()
        if img is None: return ui.div('Your new look appears here', class_='empty')
        if error: return ui.div('Choose a look or upload a valid LUT', class_='empty')
        return photo_tag(apply_filter(img, 'custom' if input.preset() in LUT_FILES else input.preset(), input.intensity(), cube))

    @render.ui
    def save():
        img, _ = source()
        _, error = lut()
        if img is None or error: return ui.tags.button('Download PNG', disabled=True, class_='disabled-download')
        return ui.download_button('download', 'Download PNG', class_='download')

    @render.download(filename='lut-studio.png', media_type='image/png')
    def download():
        img, error = source()
        cube, lut_error = lut()
        req(img is not None, not error, not lut_error)
        yield png_bytes(apply_filter(img, 'custom' if input.preset() in LUT_FILES else input.preset(), input.intensity(), cube))


app = App(app_ui, server)
