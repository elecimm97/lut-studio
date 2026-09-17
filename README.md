# LUT Studio

A photo editor built with Shiny for Python, Pillow and NumPy. Explore 51 bundled Timeless LUTs, use the built-in color filters, or load a custom `.cube` file. Adjust intensity and download a full-resolution PNG.

In the published version, Python and image processing run in the visitor's browser. The app does not upload photos to a Python server.


## Supported images and filters

Still PNG, JPEG and WebP images up to 20 MB and 16 megapixels. Preview images are resized to at most 1200 pixels per side; downloads preserve the input resolution. Alpha and EXIF orientation are preserved, embedded ICC profiles are converted to sRGB, and export omits original metadata. This is not a RAW or HDR pipeline.

Custom 3D `.cube` LUTs support sizes 2–65 and optional domains. Combined 1D/3D LUTs are rejected. Reset selects Original at 0%; raise intensity again when choosing another look.

The bundled Timeless LUT collection comes from the supplied project. Its redistribution permissions have not been verified. No license for the project has been selected.

