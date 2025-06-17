from PIL import Image
import struct

class ARGB8888:
    @staticmethod
    def read(file_path, width, height):
        with open(file_path, 'rb') as f:
            data = f.read(width * height * 4)

        pixels = []
        for i in range(0, len(data), 4):
            temp = struct.unpack('<I', data[i:i+4])[0]
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


# 编码示例：
# if __name__ == "__main__":
    # 将图像保存为ARGB8888格式
    # input_png_path = "/content/UI_SEEDPACKETS_2048_1536_2048_4096.png"
    # image = Image.open(input_png_path).convert("RGBA")
    # ARGB8888.write(image, 'output.ptx')

# 解码示例：
if __name__ == "__main__":
    # 配置图像参数
    ptx_path = "/content/UI_SEEDPACKETS_1536_00.PTX"
    output_path = 'UI_SEEDPACKETS.png'
    width  = 2048      # 2048
    height = 4096      # 4096  # 你需要确认高度！
    # 解码并保存为 PNG
    image = ARGB8888.read(ptx_path, width, height)
    image.save(output_path)
    print("转换完成，PNG 保存为:", output_path)
