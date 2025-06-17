class Color:
    """
    一个简单的颜色类来模仿System.Drawing.Color.
    假设 ARGB.
    """
    def __init__(self, a, r, g, b):
        self.A = a
        self.R = r
        self.G = g
        self.B = b

    @classmethod
    def from_argb(cls, argb_int):
        a = (argb_int >> 24) & 0xFF
        r = (argb_int >> 16) & 0xFF
        g = (argb_int >> 8) & 0xFF
        b = argb_int & 0xFF
        return cls(a, r, g, b)

    def to_argb(self):
        return (self.A << 24) | (self.R << 16) | (self.G << 8) | self.B

    @property
    def White(self):
        return Color(255, 255, 255, 255)

    @property
    def Black(self):
        return Color(255, 0, 0, 0)

    def __repr__(self):
        return f"Color(A={self.A}, R={self.R}, G={self.G}, B={self.B})"

class ETC1:
    ETC1Modifiers = [	
        [2, 8],
        [5, 17],
        [9, 29],
        [13, 42],
        [18, 60],
        [24, 80],
        [33, 106],
        [47, 183]
    ]

    @staticmethod
    def _gen_modifier(pixels):
        max_color = Color(0, 0, 0, 0).White # Initialize with a white color
        min_color = Color(0, 0, 0, 0).Black # Initialize with a black color
        min_y = float('inf')
        max_y = float('-inf')

        for pixel in pixels:
            if pixel.A == 0:
                continue
            y = (pixel.R + pixel.G + pixel.B) // 3
            if y > max_y:
                max_y = y
                max_color = pixel
            if y < min_y:
                min_y = y
                min_color = pixel

        diff_mean = ((max_color.R - min_color.R) + (max_color.G - min_color.G) + (max_color.B - min_color.B)) // 3

        mod_diff = float('inf')
        modifier = -1
        mode = -1

        for i in range(8):
            ss = ETC1.ETC1Modifiers[i][0] * 2
            sb = ETC1.ETC1Modifiers[i][0] + ETC1.ETC1Modifiers[i][1]
            bb = ETC1.ETC1Modifiers[i][1] * 2

            ss = min(ss, 255)
            sb = min(sb, 255)
            bb = min(bb, 255)

            if abs(diff_mean - ss) < mod_diff:
                mod_diff = abs(diff_mean - ss)
                modifier = i
                mode = 0
            if abs(diff_mean - sb) < mod_diff:
                mod_diff = abs(diff_mean - sb)
                modifier = i
                mode = 1
            if abs(diff_mean - bb) < mod_diff:
                mod_diff = abs(diff_mean - bb)
                modifier = i
                mode = 2

        if mode == 1:
            div1 = float(ETC1.ETC1Modifiers[modifier][0]) / float(ETC1.ETC1Modifiers[modifier][1])
            div2 = 1.0 - div1
            base_color = Color(255, 
                               int(min_color.R * div1 + max_color.R * div2), 
                               int(min_color.G * div1 + max_color.G * div2), 
                               int(min_color.B * div1 + max_color.B * div2))
        else:
            base_color = Color(255, 
                               (min_color.R + max_color.R) // 2, 
                               (min_color.G + max_color.G) // 2, 
                               (min_color.B + max_color.B) // 2)
        
        return base_color, modifier

    @staticmethod
    def _gen_horizontal(colors):
        data = 0
        data = ETC1._set_flip_mode(data, False)
        
        # Left
        left_colors = ETC1._get_left_colors(colors)
        base_c1, mod = ETC1._gen_modifier(left_colors)
        data = ETC1._set_table1(data, mod)
        data = ETC1._gen_pix_diff(data, left_colors, base_c1, mod, 0, 2, 0, 4)

        # Right
        right_colors = ETC1._get_right_colors(colors)
        base_c2, mod = ETC1._gen_modifier(right_colors)
        data = ETC1._set_table2(data, mod)
        data = ETC1._gen_pix_diff(data, right_colors, base_c2, mod, 2, 4, 0, 4)
        
        data = ETC1._set_base_colors(data, base_c1, base_c2)
        return data

    @staticmethod
    def _gen_vertical(colors):
        data = 0
        data = ETC1._set_flip_mode(data, True)

        # Top
        top_colors = ETC1._get_top_colors(colors)
        base_c1, mod = ETC1._gen_modifier(top_colors)
        data = ETC1._set_table1(data, mod)
        data = ETC1._gen_pix_diff(data, top_colors, base_c1, mod, 0, 4, 0, 2)

        # Bottom
        bottom_colors = ETC1._get_bottom_colors(colors)
        base_c2, mod = ETC1._gen_modifier(bottom_colors)
        data = ETC1._set_table2(data, mod)
        data = ETC1._gen_pix_diff(data, bottom_colors, base_c2, mod, 0, 4, 2, 4)
        
        data = ETC1._set_base_colors(data, base_c1, base_c2)
        return data

    @staticmethod
    def _get_score(original, encode):
        diff = 0
        for i in range(4 * 4):
            diff += abs(encode[i].R - original[i].R)
            diff += abs(encode[i].G - original[i].G)
            diff += abs(encode[i].B - original[i].B)
        return diff

    @staticmethod
    def gen_etc1(colors):
        horizontal = ETC1._gen_horizontal(colors)
        vertical = ETC1._gen_vertical(colors)
        
        horizontal_score = ETC1._get_score(colors, ETC1.decode_etc1(horizontal))
        vertical_score = ETC1._get_score(colors, ETC1.decode_etc1(vertical))
        
        return horizontal if horizontal_score < vertical_score else vertical

    @staticmethod
    def _gen_pix_diff(data, pixels, base_color, modifier, x_offs, x_end, y_offs, y_end):
        base_mean = (base_color.R + base_color.G + base_color.B) // 3
        i = 0
        for yy in range(y_offs, y_end):
            for xx in range(x_offs, x_end):
                diff = ((pixels[i].R + pixels[i].G + pixels[i].B) // 3) - base_mean

                if diff < 0:
                    data |= (1 << (xx * 4 + yy + 16))
                
                tbldiff1 = abs(diff) - ETC1.ETC1Modifiers[modifier][0]
                tbldiff2 = abs(diff) - ETC1.ETC1Modifiers[modifier][1]

                if abs(tbldiff2) < abs(tbldiff1):
                    data |= (1 << (xx * 4 + yy))
                i += 1
        return data

    @staticmethod
    def _get_left_colors(pixels):
        left = [None] * (4 * 2)
        for y in range(4):
            for x in range(2):
                left[y * 2 + x] = pixels[y * 4 + x]
        return left

    @staticmethod
    def _get_right_colors(pixels):
        right = [None] * (4 * 2)
        for y in range(4):
            for x in range(2, 4):
                right[y * 2 + x - 2] = pixels[y * 4 + x]
        return right

    @staticmethod
    def _get_top_colors(pixels):
        top = [None] * (4 * 2)
        for y in range(2):
            for x in range(4):
                top[y * 4 + x] = pixels[y * 4 + x]
        return top

    @staticmethod
    def _get_bottom_colors(pixels):
        bottom = [None] * (4 * 2)
        for y in range(2, 4):
            for x in range(4):
                bottom[(y - 2) * 4 + x] = pixels[y * 4 + x]
        return bottom

    @staticmethod
    def _set_flip_mode(data, mode):
        data &= ~(1 << 32)
        data |= (1 if mode else 0) << 32
        return data

    @staticmethod
    def _set_diff_mode(data, mode):
        data &= ~(1 << 33)
        data |= (1 if mode else 0) << 33
        return data

    @staticmethod
    def _set_table1(data, table):
        data &= ~(7 << 37)
        data |= (table & 0x7) << 37
        return data

    @staticmethod
    def _set_table2(data, table):
        data &= ~(7 << 34)
        data |= (table & 0x7) << 34
        return data

    @staticmethod
    def _set_base_colors(data, color1, color2):
        r1 = color1.R
        g1 = color1.G
        b1 = color1.B
        r2 = color2.R
        g2 = color2.G
        b2 = color2.B

        r_diff = (r2 - r1) // 8
        g_diff = (g2 - g1) // 8
        b_diff = (b2 - b1) // 8

        if -4 < r_diff < 3 and -4 < g_diff < 3 and -4 < b_diff < 3:
            data = ETC1._set_diff_mode(data, True)
            r1 //= 8
            g1 //= 8
            b1 //= 8
            data |= (r1) << 59
            data |= (g1) << 51
            data |= (b1) << 43
            data |= (r_diff & 0x7) << 56
            data |= (g_diff & 0x7) << 48
            data |= (b_diff & 0x7) << 40
        else:
            data = ETC1._set_diff_mode(data, False) # Explicitly set diff mode to false
            data |= (r1 // 0x11) << 60
            data |= (g1 // 0x11) << 52
            data |= (b1 // 0x11) << 44

            data |= (r2 // 0x11) << 56
            data |= (g2 // 0x11) << 48
            data |= (b2 // 0x11) << 40
        return data

    @staticmethod
    def decode_etc1(data, alpha=~0):
        result = [None] * (4 * 4)
        diff_bit = ((data >> 33) & 1) == 1
        flip_bit = ((data >> 32) & 1) == 1

        if diff_bit:
            r = (data >> 59) & 0x1F
            g = (data >> 51) & 0x1F
            b = (data >> 43) & 0x1F
            r1 = (r << 3) | ((r & 0x1C) >> 2)
            g1 = (g << 3) | ((g & 0x1C) >> 2)
            b1 = (b << 3) | ((b & 0x1C) >> 2)

            # Python handles negative shifts differently, explicitly sign extend for 3-bit signed
            r_diff_raw = (data >> 56) & 0x7
            g_diff_raw = (data >> 48) & 0x7
            b_diff_raw = (data >> 40) & 0x7

            # Sign extension for 3-bit value
            r_diff = r_diff_raw - 8 if r_diff_raw & 0x4 else r_diff_raw
            g_diff = g_diff_raw - 8 if g_diff_raw & 0x4 else g_diff_raw
            b_diff = b_diff_raw - 8 if b_diff_raw & 0x4 else b_diff_raw

            r += r_diff
            g += g_diff
            b += b_diff
            r2 = (r << 3) | ((r & 0x1C) >> 2)
            g2 = (g << 3) | ((g & 0x1C) >> 2)
            b2 = (b << 3) | ((b & 0x1C) >> 2)
        else:
            r1 = ((data >> 60) & 0xF) * 0x11
            g1 = ((data >> 52) & 0xF) * 0x11
            b1 = ((data >> 44) & 0xF) * 0x11
            r2 = ((data >> 56) & 0xF) * 0x11
            g2 = ((data >> 48) & 0xF) * 0x11
            b2 = ((data >> 40) & 0xF) * 0x11
        
        table1 = (data >> 37) & 0x7
        table2 = (data >> 34) & 0x7

        for y3 in range(4):
            for x3 in range(4):
                val = (data >> (x3 * 4 + y3)) & 0x1
                neg = ((data >> (x3 * 4 + y3 + 16)) & 0x1) == 1
                
                a = ((alpha >> ((x3 * 4 + y3) * 4)) & 0xF) * 0x11

                if (flip_bit and y3 < 2) or (not flip_bit and x3 < 2):
                    add = ETC1.ETC1Modifiers[table1][val] * (-1 if neg else 1)
                    r_val = ETC1._color_clamp(r1 + add)
                    g_val = ETC1._color_clamp(g1 + add)
                    b_val = ETC1._color_clamp(b1 + add)
                else:
                    add = ETC1.ETC1Modifiers[table2][val] * (-1 if neg else 1)
                    r_val = ETC1._color_clamp(r2 + add)
                    g_val = ETC1._color_clamp(g2 + add)
                    b_val = ETC1._color_clamp(b2 + add)
                
                result[y3 * 4 + x3] = Color(a, r_val, g_val, b_val)
        return result

    @staticmethod
    def _color_clamp(color_val):
        return max(0, min(255, color_val))

