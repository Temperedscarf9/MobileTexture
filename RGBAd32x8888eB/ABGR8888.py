import struct
import numpy as np
from PIL import Image


class ABGR8888:
    @staticmethod
    def read(file_path, width, height):
        """
        从二进制文件读取 ABGR8888 格式图像数据并返回 PIL 图像
        """
        with open(file_path, 'rb') as f:
            data = f.read(width * height * 4)

        pixels = []
        for i in range(0, len(data), 4):
            temp = struct.unpack('<I', data[i:i+4])[0]
            r = temp & 0xFF
            g = (temp >> 8) & 0xFF
            b = (temp >> 16) & 0xFF
            a = (temp >> 24) & 0xFF
            pixels.append((r, g, b, a))

        img = Image.new("RGBA", (width, height))
        img.putdata(pixels)
        return img

    @staticmethod
    def write(image: Image.Image, file_path):
        """
        将 PIL 图像保存为 ABGR8888 二进制格式
        """
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        pixels = list(image.getdata())

        with open(file_path, 'wb') as f:
            for r, g, b, a in pixels:
                packed = (a << 24) | (b << 16) | (g << 8) | r
                f.write(struct.pack('<I', packed))
