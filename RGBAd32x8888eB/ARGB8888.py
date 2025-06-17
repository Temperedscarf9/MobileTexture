from PIL import Image
import struct

class ARGB8888:
    @staticmethod
    def read(file_path, width, height,block=4):
        with open(file_path, 'rb') as f:
            data = f.read(width * height * block)

        pixels = []
        for i in range(0, len(data), block):
            temp = struct.unpack('<I', data[i:i+block])[0]
            a = (temp >> 24) & 0xFF
            r = (temp >> 16) & 0xFF
            g = (temp >> 8) & 0xFF
            b = temp & 0xFF
            pixels.append((r, g, b, a))  # PIL expects RGBA

        img = Image.new('RGBA', (width, height))
        img.putdata(pixels)
        return img
    @staticmethod
    def write(image: Image.Image, file_path: str):
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        pixels = list(image.getdata())
        data = bytearray()

        for r, g, b, a in pixels:
            argb = (a << 24) | (r << 16) | (g << 8) | b
            data.extend(struct.pack('<I', argb))

        with open(file_path, 'wb') as f:
            f.write(data)
