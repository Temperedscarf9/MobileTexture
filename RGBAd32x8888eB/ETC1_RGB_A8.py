def write_etc1_rgb_a8(file_path, width, height, image: Image.Image):
    """
    将 RGBA 图像编码为 ETC1 RGB 数据，并分离 A8 alpha 数据，
    然后将其写入指定文件

    参数：
        file_path (str)：输出文件的路径。
        width (int)：图像的宽度。
        height (int)：图像的高度。
        image (Image.Image)：RGBA 格式的 Pillow 图像对象。
    """
    # 确保图像为 RGBA 格式
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    
    img_data = list(image.getdata())

    # 对于 ETC1 块处理，Pad 图像尺寸应为 4 的倍数
    padded_width = (width + 3) // 4 * 4
    padded_height = (height + 3) // 4 * 4

    etc1_blocks = []
    alpha_data = bytearray() # To store alpha bytes

    # --- ETC1区块处理 ---
    # Iterate through 4x4 blocks
    for by in range(0, padded_height, 4):
        for bx in range(0, padded_width, 4):
            block_pixels_etc1 = [] # For ETC1 RGB compression
            
            # 提取当前 4x4 块的像素
            for y in range(4):
                for x in range(4):
                    ix = bx + x
                    iy = by + y
                    
                    if ix < width and iy < height:
                        # 像素为 (R, G, B, A)，来自 PIL
                        # 为 ETC1 处理创建自定义颜色对象
                        r, g, b, a = img_data[iy * width + ix]
                        block_pixels_etc1.append(Color(a, r, g, b))
                    else:
                        # 用透明黑色/无色填充超出范围的像素
                        # ETC1 只关心 RGB，因此这里的 alpha 主要是一个占位符
                        block_pixels_etc1.append(Color(0, 0, 0, 0))
            
            # 调用 gen_etc1 压缩 4x4 块
            # 这将返回一个 64 位（8 字节）整数，表示压缩块
            etc1_block_val = ETC1.gen_etc1(block_pixels_etc1)
            
            # 附加 ETC1 块的 8 个字节（ETC1 文件中常用的小端字节序）
            etc1_blocks.append(etc1_block_val.to_bytes(8, 'big'))

    # --- Alpha 通道处理 (A8) ---
    # 遍历每个像素以提取其 alpha 值
    for iy in range(height):
        for ix in range(width):
            # img_data 已经是 (R, G, B, A)
            alpha = img_data[iy * width + ix][3]
            alpha_data.append(alpha)

    # --- 写入文件 ---
    with open(file_path, 'wb') as f:
        # 首先写入ETC1 RGB块
        for block_bytes in etc1_blocks:
            f.write(block_bytes)

        # 然后写入A8 alpha数据
        f.write(alpha_data)

# === 主程序入口 ===
# === Main Program Entry ===
def compress_png_to_etc1_rgb_a8(input_png_path, output_ptx_path):
    """
    Compresses a PNG image to ETC1 RGB and A8 alpha format, saving it to a .ptx file.

    Args:
        input_png_path (str): Path to the input PNG image.
        output_ptx_path (str): Path for the output .ptx file.
    """
    try:
        image = Image.open(input_png_path).convert("RGBA")
        width, height = image.size
        
        write_etc1_rgb_a8(output_ptx_path, width, height, image)
        print(f"Compression complete. Output saved to: {output_ptx_path}")
    except FileNotFoundError:
        print(f"Error: Input PNG file not found at '{input_png_path}'")
    except Exception as e:
        print(f"An error occurred during compression: {e}")

# Example Usage:
# Make sure you have a PNG file at this path or replace it with one that exists.
# This assumes you're running this in an environment like Google Colab where /content/
# is a common path for uploaded files.
compress_png_to_etc1_rgb_a8("/content/ZOMBIEBEACHZOMBOSSGROUP_768.png", "output222.ptx")
