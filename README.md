# LUT Studio

A photo editor built with Shiny for Python, Pillow and NumPy. Explore 51 bundled Timeless LUTs, use the built-in color filters, or load a custom `.cube` file. Adjust intensity and download a full-resolution PNG.

This version includes a **Shinylive export workflow for GitHub Pages**. In the published version, Python and image processing run in the visitor's browser. The app does not upload photos to a Python server.

## Publish on GitHub Pages

1. Create a public repository named `lut-studio` with the default branch `main`.
2. Upload this folder's contents to the repository root. `app.py`, `imaging.py`, `style.css`, `theme.js`, `requirements.txt`, `docs/`, and `luts/` must keep their current names and structure. Upload the extracted files, not the ZIP.
3. In **Settings → Pages → Build and deployment → Source**, select **GitHub Actions**.
4. Make sure `.github/workflows/publish.yml` exists. Finder hides dot-prefixed files: press **Command + Shift + .** to show them. Alternatively, create this exact path using GitHub's **Add file → Create new file** and paste the supplied workflow.
5. Open the repository's **Actions** tab, select **Publish LUT Studio**, and click **Run workflow** on `main`.
6. Open the link in the successful `publish` job. With account `elecimm97` and repository `lut-studio`, the expected address is `https://elecimm97.github.io/lut-studio/`.

Every subsequent commit to `main` rebuilds and publishes the app. This repository is separate from the portfolio repository.

## Edit

- `app.py`: English interface, controls and creator's portfolio link (`CREATOR_URL`).
- `imaging.py`: image validation, filters and LUT processing.
- `style.css`: appearance, layout and colors.
- `theme.js`: light/dark preference.
- `luts/`: bundled `.cube` files; add or remove files to change the menu.
- `docs/sample.png`: sample image.

The first visit downloads Python and the filters, so loading can take longer than a simple portfolio page. Performance depends on the visitor's device; start with smaller images on mobile.

## Preview locally

Use Python 3.12 and a fresh virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install shinylive==0.8.12
shinylive export . _site
python -m http.server --directory _site 8008
```

Open `http://localhost:8008/`. Opening `_site/index.html` directly from Finder does not work. The export installs the browser-compatible versions included in Shinylive; `requirements.txt` intentionally does not pin the original desktop versions. The verified bundle uses Shiny 1.8.0, Pillow 10.2.0 and NumPy 2.0.2.

To run as a conventional local Python server instead:

```sh
python -m pip install -r requirements.txt
python -m shiny run app.py
```

In conventional server mode, image processing happens on that Python server.

## Supported images and filters

Still PNG, JPEG and WebP images up to 20 MB and 16 megapixels. Preview images are resized to at most 1200 pixels per side; downloads preserve the input resolution. Alpha and EXIF orientation are preserved, embedded ICC profiles are converted to sRGB, and export omits original metadata. This is not a RAW or HDR pipeline.

Custom 3D `.cube` LUTs support sizes 2–65 and optional domains. Combined 1D/3D LUTs are rejected. Reset selects Original at 0%; raise intensity again when choosing another look.

The bundled Timeless LUT collection comes from the supplied project. Its redistribution permissions have not been verified. No license for the project has been selected.

## Verification

Nine image-processing tests passed. The static Shinylive export was tested locally at a subdirectory URL: startup, sample image, a bundled LUT, light/dark switching and reset worked. The downloaded PNG matched the expected filtered image pixel for pixel. The automated browser file picker did not complete, so uploading photos and custom LUTs still needs a manual check. No repository or public deployment was created by this preparation.

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```
