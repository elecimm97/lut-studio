import unittest
from io import BytesIO
import numpy as np
from PIL import Image
from imaging import apply_filter, read_cube, load_image, png_bytes


def cube_text(fn=lambda r,g,b:(r,g,b), domain=''):
    return 'TITLE "Test"\nLUT_3D_SIZE 2\n'+domain+'\n'+'\n'.join(' '.join(map(str,fn(r,g,b))) for b in (0,1) for g in (0,1) for r in (0,1))


class ImagingTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.fromarray(np.array([[[23, 110, 209, 82], [255,0,40,0]], [[41,52,63,255],[0,255,0,128]]], dtype=np.uint8))

    def test_identity_lut(self):
        np.testing.assert_array_equal(apply_filter(self.image,'custom',100,read_cube(cube_text())), self.image)

    def test_channel_order_interpolation_and_blend(self):
        cube=read_cube(cube_text(lambda r,g,b:(b,1-g,r)))
        result=np.array(apply_filter(self.image,'custom',100,cube))
        np.testing.assert_array_equal(result[0,0], [209,145,23,82])
        mixed=np.array(apply_filter(self.image,'custom',50,cube))
        np.testing.assert_allclose(mixed[0,0], [116,128,116,82],atol=1)

    def test_zero_and_original_preserve_pixels(self):
        np.testing.assert_array_equal(apply_filter(self.image,'amber',0),self.image)
        np.testing.assert_array_equal(apply_filter(self.image,'original',100),self.image)

    def test_alpha_preserved_all_presets(self):
        for preset in ['amber','ocean','mono','fade']:
            np.testing.assert_array_equal(np.array(apply_filter(self.image,preset,85))[...,3], np.array(self.image)[...,3])

    def test_domain(self):
        cube=read_cube(cube_text(domain='DOMAIN_MIN 0 0 0\nDOMAIN_MAX 0.5 0.5 0.5'))
        result=np.array(apply_filter(self.image,'custom',100,cube))
        np.testing.assert_allclose(result[0,0,:3],[46,220,255],atol=1)

    def test_bad_luts(self):
        for text in ['LUT_3D_SIZE 2\n0 0 0',cube_text().replace('0 0 0','nan 0 0'),cube_text(domain='DOMAIN_MAX 0 0 0'),'LUT_1D_SIZE 2', 'LUT_3D_SIZE 1000']:
            with self.assertRaises(ValueError): read_cube(text)

    def test_image_roundtrip(self):
        decoded=load_image(BytesIO(png_bytes(self.image)))
        np.testing.assert_array_equal(decoded,self.image)

    def test_invalid_image(self):
        with self.assertRaises(ValueError): load_image(BytesIO(b'not a photo'))

    def test_orientation(self):
        image=Image.new('RGB',(4,2),'red')
        exif=Image.Exif();exif[274]=6
        buf=BytesIO();image.save(buf,format='JPEG',exif=exif);buf.seek(0)
        self.assertEqual(load_image(buf).size,(2,4))

if __name__=='__main__': unittest.main()
