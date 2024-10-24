# d2_convert.py

`d2_convert.py` is a Python tool used to convert image files to binary format for use with specific image data and palette formats. It provides options for adding headers, applying RLE encoding, using alpha masks, and more.

## Usage

```sh
python d2_convert.py <input_file> <binary_file> [-r] [-m] [-c <color_format>] [-p <palette_format>]
```

## Options

| Option                   | Description                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| `-c <color_format>`        | Output `<binary_file>` as image data in `<color_format>` format.             |
| `-p <palette_format>`      | Output `<binary_file>` as palette data in `<palette_format>` format.         |
| `-h`                       | Add a header ('D', '2', u16 width, u16 height, u8 flags, u8 type, u16 mode, u16 length). |
| `-f <value>`               | Flags value to place in the header (must be used with `-h` option).          |
| `-t <value>`               | Type value to place in the header (must be used with `-h` option).           |
| `-l`                       | Output a LUT PNG of the palette (must be used with `-p` option).             |
| `-r`                       | Apply RLE encoding.                                                         |
| `-m`                       | Use alpha channel from a mask file (should be called `<input_file>_mask.png`).|

## Supported Color Formats

- d2_mode_argb8888 (default)
- d2_mode_rgb565
- d2_mode_ai44
- d2_mode_i8
- d2_mode_i4
- d2_mode_i2
- d2_mode_i1

## Supported Palette Formats

- d2_mode_rgba8888 (default)
- d2_mode_rgb565

## Example

Convert an image file with RLE encoding and output in d2_mode_rgb565 format:

```sh
python d2_convert.py input.png output.bin -r -c d2_mode_rgb565
```

## Credits

- [benbaker76](https://github.com/benbaker76) for writing the software, updating and maintaining it.

## License

This project is licensed under the MIT License.