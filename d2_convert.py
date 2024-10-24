import os
import sys
from PIL import Image
import struct

d2_mode_alpha8 = 0
d2_mode_rgb565 = 1
d2_mode_argb8888 = 2
d2_mode_argb4444 = 3
d2_mode_argb1555 = 4
d2_mode_ai44 = 5
d2_mode_rgba8888 = 6
d2_mode_rgba4444 = 7
d2_mode_rgba5551 = 8
d2_mode_i8 = 9
d2_mode_i4 = 10
d2_mode_i2 = 11
d2_mode_i1 = 12
d2_mode_alpha4 = 13
d2_mode_alpha2 = 14
d2_mode_alpha1 = 15
# following additional flags can be ored together with previous modes:
d2_mode_rle = 16     # RLE decoder is used
d2_mode_clut = 32    # CLUT 256 is used

class Color:
    def __init__(self, r, g, b, a=None):
        self.R = r
        self.G = g
        self.B = b
        self.A = a

def get_d2_mode(color_format, use_rle):
    mode_dict = {
        "d2_mode_alpha8": d2_mode_alpha8,
        "d2_mode_rgb565": d2_mode_rgb565,
        "d2_mode_argb8888": d2_mode_argb8888,
        "d2_mode_argb4444": d2_mode_argb4444,
        "d2_mode_argb1555": d2_mode_argb1555,
        "d2_mode_ai44": d2_mode_ai44,
        "d2_mode_rgba8888": d2_mode_rgba8888,
        "d2_mode_rgba4444": d2_mode_rgba4444,
        "d2_mode_rgba5551": d2_mode_rgba5551,
        "d2_mode_i8": d2_mode_i8,
        "d2_mode_i4": d2_mode_i4,
        "d2_mode_i2": d2_mode_i2,
        "d2_mode_i1": d2_mode_i1,
        "d2_mode_alpha4": d2_mode_alpha4,
        "d2_mode_alpha2": d2_mode_alpha2,
        "d2_mode_alpha1": d2_mode_alpha1
    }
    mode_value = mode_dict.get(color_format, None)
    
    if mode_value is None:
        raise ValueError("Invalid color mode")

    if mode_value == d2_mode_ai44 or (mode_value >= d2_mode_i8 and mode_value <= d2_mode_i1):
        mode_value |= d2_mode_clut

    if use_rle:
        mode_value |= d2_mode_rle

    return mode_value

def append_header(data, width, height, flags, type, mode, length):
    data.extend(struct.pack('B', ord('D')))
    data.extend(struct.pack('B', ord('2')))
    data.extend(struct.pack('H', width))
    data.extend(struct.pack('H', height))
    data.extend(struct.pack('B', flags))
    data.extend(struct.pack('B', type))
    data.extend(struct.pack('H', mode))
    data.extend(struct.pack('I', length))

def format_byte_array(byte_array):
    hex_string = ' '.join([f'{byte:02X}' for byte in byte_array])
    formatted_hex = '\n'.join([hex_string[i:i+48] for i in range(0, len(hex_string), 48)])
    print(formatted_hex)

def rle_encode(buffer):
    repeat = 0
    direct = 0
    from_index = 0
    encoded = []

    for x in range(1, len(buffer)):
        if buffer[x-1] != buffer[x]:
            # next pixel is different
            if repeat:
                encoded.append(128 + repeat)
                encoded.append(buffer[from_index])
                from_index = x
                repeat = 0
                direct = 0
            else:
                direct += 1
        else:
            # next pixel is the same
            if direct:
                encoded.append(direct - 1)
                encoded.extend(buffer[from_index:from_index+direct])
                from_index = x
                direct = 0
                repeat = 1
            else:
                repeat += 1

        if repeat == 128:
            encoded.append(255)
            encoded.append(buffer[from_index])
            from_index = x
            direct = 0
            repeat = 0
        elif direct == 128:
            encoded.append(127)
            encoded.extend(buffer[from_index:from_index+direct])
            from_index = x
            direct = 0
            repeat = 0

    if repeat > 0:
        encoded.append(128 + repeat)
        encoded.append(buffer[from_index])
    else:
        encoded.append(direct)
        encoded.extend(buffer[from_index:from_index+direct+1])

    return encoded

def read_palette(file_path):
    _, extension = os.path.splitext(file_path.lower())
    if extension == '.act':
        return read_act_palette(file_path)
    elif extension == '.png':
        return read_png_palette(file_path)
    else:
        print("Unsupported file format:", extension)
        sys.exit(0)

def read_act_palette(file_path):
    color_palette = [Color(0, 0, 0) for _ in range(256)]
    try:
        with open(file_path, 'rb') as act_file:
            for i in range(256):
                color_palette[i].R, color_palette[i].G, color_palette[i].B = struct.unpack('BBB', act_file.read(3))
    
            current_position = act_file.tell()
            act_file.seek(0, 2)
            end_position = act_file.tell()
            act_file.seek(current_position)
    
            if current_position == end_position - 4:
                pal_count, alpha_index = struct.unpack('hh', act_file.read(4))
                transparent_index = alpha_index
                color_palette = color_palette[:pal_count]
            else:
                transparent_index = 0

        return color_palette, transparent_index
    except Exception as e:
        print("Failed to read .act file", file_path)
        print(e)
        sys.exit(0)

def read_png_palette(file_path):
    try:
        im = Image.open(file_path)
    except Exception as e:
        print("Fail to open png file", file_path)
        print(e)
        sys.exit(0)

    mode = im.mode

    if mode != 'P':
        print("The PNG file is not in indexed mode.")
        sys.exit(0)

    palette = []
    transparent_index = im.info['transparency'] if 'transparency' in im.info else None
    palette_raw = im.getpalette()
    
    for i in range(0, len(palette_raw), 3):
        palette.append(Color(palette_raw[i], palette_raw[i + 1], palette_raw[i + 2], 255))

    return palette, len(palette), transparent_index

def write_palette(binary_file, palette, palette_format):
    palette_filename = binary_file[:-4] + ".pal"
    with open(palette_filename, "wb") as palette_file:
        for entry in palette:
            if palette_format == "d2_mode_argb8888":
                rgb = (entry.R << 16) | (entry.G << 8) | entry.B
                palette_file.write(struct.pack('I', rgb))
            else:
                R = (entry.R * 31) // 255
                G = (entry.G * 63) // 255
                B = (entry.B * 31) // 255
                rgb = (R << 11) | (G << 5) | B
                palette_file.write(struct.pack('H', rgb))

    print("Palette file \"%s\"" % palette_filename, "generated with format:", palette_format)

def write_lut(input_file, palette):
    lut_filename = os.path.splitext(input_file)[0] + ".png"

    palette_length = len(palette)
    image_size = (palette_length, 1)

    image = Image.new("RGBA", image_size)

    for i, entry in enumerate(palette):
        color = (entry.R, entry.G, entry.B, 255)
        image.putpixel((i, 0), color)

    image.save(lut_filename)

    print(f"LUT file \"{lut_filename}\" generated.")

def convert_to_binary(input_file, binary_file, color_format="d2_mode_argb8888", palette_format="d2_mode_argb8888", add_header=False, flags=0, type=0, output_lut=False, use_rle=False, use_mask=False):
    is_indexed = (color_format == "d2_mode_i1" or color_format == "d2_mode_i2" or color_format == "d2_mode_i4" or color_format == "d2_mode_i8" or color_format == "d2_mode_ai44")
    
    if palette_format != None:
        palette, transparent_index = read_palette(input_file)

    mask = None
    mask_im = None
    if use_mask:
        try:
            mask_file = input_file[:-4] + "_mask.png"
            mask = Image.open(mask_file)
            if mask.mode != 'RGBA':
                print("The mask file is not in RGBA mode.")
                sys.exit(0)
            mask_im = mask.load()
        except Exception as e:
            print("Fail to open mask file", mask_file)
            print(e)
            sys.exit(0)

    if input_file.lower().endswith('.png'):
        d2_data = bytearray()
        image_data = bytearray()
        im = Image.open(input_file)
        image_width = im.size[0]
        image_height = im.size[1]
        pix = im.load()
        
        for h in range(image_height):
            row_data = bytearray()
            byte_value = 0  # Initialize the byte value for indexed modes
            bit_count = 0

            for w in range(image_width):
                if w < im.size[0]:
                    if im.mode == "P":  # Check if the image is indexed                        
                        index = pix[w, h]
                        A = 255  # Default alpha for indexed modes
                    elif im.mode == "RGB":
                        R = pix[w, h][0]
                        G = pix[w, h][1]
                        B = pix[w, h][2]
                        A = 255
                    elif im.mode == "RGBA":
                        R = pix[w, h][0]
                        G = pix[w, h][1]
                        B = pix[w, h][2]
                        A = pix[w, h][3]  # Alpha channel value

                        # Adjust RGB values based on alpha channel
                        R = (R * A) // 255
                        G = (G * A) // 255
                        B = (B * A) // 255
                    else:
                        print("Image mode not supported:", im.mode)
                        sys.exit(0)

                    if color_format == "d2_mode_i1":
                        byte_value |= (index & 0x01) << bit_count
                        index <<= 1
                        bit_count += 1
                    elif color_format == "d2_mode_i2":
                        byte_value |= (index & 0x03) << bit_count
                        index <<= 2
                        bit_count += 2
                    elif color_format == "d2_mode_i4":
                        byte_value |= (index & 0x0f) << bit_count
                        index <<= 4
                        bit_count += 4
                    elif color_format == "d2_mode_i8":
                        byte_value = index & 0xff
                        bit_count = 8
                    elif color_format == "d2_mode_ai44":
                        A = mask_im[w, h][3] if mask_im is not None else A
                        byte_value = ((A >> 4) << 4) | ((index if A != 0 else 0) & 0xF)
                        bit_count = 8

                    # If we have collected 8 bits, append to row_data and reset the byte_value
                    if bit_count == 8:
                        row_data.extend(struct.pack('B', byte_value))
                        byte_value = 0
                        bit_count = 0

                    if is_indexed:
                        continue

                    if color_format == "d2_mode_argb8888":
                        rgb = (A << 24) | (R << 16) | (G << 8) | B
                        row_data.extend(struct.pack('I', rgb))
                    if color_format == "d2_mode_rgba8888":
                        rgb = (R << 24) | (G << 16) | (B << 8) | A
                        row_data.extend(struct.pack('I', rgb))
                    elif color_format == "d2_mode_rgb565":
                        R = (R * 31) // 255
                        G = (G * 63) // 255
                        B = (B * 31) // 255
                        rgb = (R << 11) | (G << 5) | B
                        row_data.extend(struct.pack('H', rgb))
                    else:
                        print("Unsupported color mode:", color_format)
                        sys.exit(0)

            if is_indexed and bit_count > 0:
                row_data.extend(struct.pack('B', byte_value))

            image_data.extend(row_data)

        if use_rle:
            original_len = len(image_data)
            image_data = rle_encode(image_data)
            print("Original size %d" % original_len, "bytes RLE compressed to %d bytes" % len(image_data))

        if add_header:
            append_header(d2_data, image_width, image_height, flags, type, get_d2_mode(color_format, use_rle), len(image_data))
            
        d2_data.extend(image_data);

        with open(binary_file, "wb") as file:
            file.write(d2_data)

    if palette_format != None:
        write_palette(binary_file, palette, palette_format)

        if output_lut:
            write_lut(input_file, palette)

    print("File \"%s\"" % input_file, "converted to \"%s\"" % binary_file, "with color mode:", color_format)

def main():
    len_argument = len(sys.argv)
    if len_argument < 3:
        print("")
        print("Usage:")
        print("\tpython d2_convert.py <input_file> <binary_file> [-r] [-m] [-c <color_format>] [-p <palette_format>]")
        print("Options:")
        print("\t-c <color_format>   Output <binary_file> as image data in <color_format> format")
        print("\t-p <palette_format> Output <binary_file> as palette data in <palette_format> format")
        print("\t-h                  Add a header ('D', '2', u16 width, u16 height, u8 flags, u8 type, u16 mode, u16 length)")
        print("\t-f <value>          Flags value to place in the header (must be used with -h option)")
        print("\t-t <value>          Type value to place in the header (must be used with -h option)")
        print("\t-l                  Output a LUT png of the palette (must be used with -p option)")     
        print("\t-r                  RLE encode")
        print("\t-m                  Use alpha channel from a mask file (should be called <input_file>_mask.png)")
        print("")
        print("Supported color formats:")
        print("\td2_mode_argb8888 (default)")
        print("\td2_mode_rgb565")
        print("\td2_mode_ai44")
        print("\td2_mode_i8")
        print("\td2_mode_i4")
        print("\td2_mode_i2")
        print("\td2_mode_i1")
        print("Supported palette formats:")
        print("\td2_mode_rgba8888 (default)")
        print("\td2_mode_rgb565")
        sys.exit(0)

    input_file = sys.argv[1]
    binary_file = sys.argv[2]

    color_format = "d2_mode_argb8888"
    palette_format = None
    flags = 0
    type = 0

    if "-c" in sys.argv:
        mode_index = sys.argv.index("-c")
        if mode_index + 1 < len(sys.argv):
            color_format = sys.argv[mode_index + 1]

    if "-p" in sys.argv:
        format_index = sys.argv.index("-p")
        if format_index + 1 < len(sys.argv):
            palette_format = sys.argv[format_index + 1]

    if "-f" in sys.argv:
        format_index = sys.argv.index("-f")
        if format_index + 1 < len(sys.argv):
            flags = sys.argv[format_index + 1]

    if "-t" in sys.argv:
        format_index = sys.argv.index("-t")
        if format_index + 1 < len(sys.argv):
            type = sys.argv[format_index + 1]

    add_header = "-h" in sys.argv
    output_lut = "-l" in sys.argv
    use_rle = "-r" in sys.argv
    use_mask = "-m" in sys.argv
    
    convert_to_binary(input_file, binary_file, color_format, palette_format, add_header, flags, type, output_lut, use_rle, use_mask)

if __name__ == "__main__":
    main()
