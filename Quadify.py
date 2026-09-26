from __future__ import annotations

import os
import random
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor

from PIL import Image
from typing import ByteString, Iterable

from Vector import Vector


class Binable:
    def to_bin(self) -> bytes:
        return b''


def to_bin(binable: Btest_squares2inable | int):
    return binable.to_bin()


class ByteInt(int, Binable):
    def __init__(self, *args):
        assert self < 256, f'Value must fit in 1 byte. {self} does not fit in a byte.'

    def __add__(self, other):
        return ByteInt(int(self) + other)

    def __sub__(self, other):
        return ByteInt(int(self) - other)

    def __mul__(self, other):
        return ByteInt(int(self) * other)

    def __truediv__(self, other):
        return ByteInt(int(self) / other)

    def __floordiv__(self, other):
        return ByteInt(int(self) // other)

    def to_bin(self):
        return int(self).to_bytes(1, 'little')

    def __str__(self):
        return str(int(self)) + 'd'


class Quad(Binable):
    def __init__(self, value: ByteInt = None,
                 size: Vector[float, float] = None,
                 margin: float = 0,
                 pos: Vector[float, float] = None):
        self.used = 0
        self.margin = margin
        if value is None:
            value = ByteInt(0)
        self.value: tuple[ByteInt] | tuple[Quad, Quad, Quad, Quad] = tuple([value])
        if size is None:
            size = Vector([1.0, 1.0])
        self.size = size
        if pos is None:
            pos = Vector([0, 0])
        self.pos = pos

    def get_value(self):
        if self.is_subdivided():
            return self.value
        return self.value[0]

    def subdivide(self):
        if not self.is_subdivided():
            self.value = [Quad(self.value[0],
                               self.size / 2,
                               self.margin,
                               self.pos + (self.size / 2 * (x, y)))
                          for x in range(0, 2) for y in range(0, 2)]
        return self.value

    def includes(self, pos: Vector[float, float]):
        return self.pos <= pos < self.pos + self.size

    def is_subdivided(self):
        return len(self.value) > 1

    def put_pixel(self, at_pos: Vector[float, float], value: ByteInt, recursive=True):
        self.used += 1
        if self.used <= 1:
            self.value = [value]
            return
        if not self.is_subdivided():
            if abs(self.get_value() - value) > self.margin:
                self.subdivide()
                if recursive:
                    self.put_pixel(at_pos, value)
            else:
                self.value = [ByteInt(((self.used - 1) * int(self.get_value()) + int(value))
                                      // self.used)]
        else:
            if recursive:
                for quad in self.value:
                    if isinstance(quad, Quad):  # for the IDE
                        if quad.includes(at_pos):
                            quad.put_pixel(at_pos, value)

    def to_bin(self):
        return int(self.is_subdivided()).to_bytes(1, 'little') + b''.join(map(to_bin, reversed(self.value)))


    def get_value_at(self, pos: Vector[float, float]):
        if self.is_subdivided():
            for quad in self.value:
                if quad.includes(pos):
                    return quad.get_value_at(pos)
        return int(self.get_value())

    @staticmethod
    def from_bytes(input_bytes, size: Vector[float, float] = None) -> Quad:
        quad = Quad(size=size)
        quad_stack = [quad]
        while quad_stack and input_bytes != '':
            operating_quad = quad_stack.pop(-1)
            if input_bytes[0] == 1:
                quad_stack += operating_quad.subdivide()
                input_bytes = input_bytes[1:]
            else:
                operating_quad.value = [ByteInt(input_bytes[1])]
                input_bytes = input_bytes[2:]
        # print(quad.to_bin().decode())
        return quad

    def feed_image(self, img_load, size, channel: int):
        for x in range(*map(lambda off: int(off*size[0]), (self.pos[0], self.pos[0]+self.size[0]))):
            for y in range(*map(lambda off: int(off*size[1]), (self.pos[1], self.pos[1]+self.size[1]))):
                self.put_pixel(Vector((x, y)), ByteInt(img_load[x, y][channel]), recursive=False)
                if self.is_subdivided():
                    for quad in self.value:
                        quad.feed_image(img_load, size, channel)
                    return self
        return self


def quadify_image(img: Image.Image, margin=10, iterations=2):
    img_load = img.load()
    quads = [Quad(size=Vector(img.size), margin=margin) for _ in range(len(img_load[0, 0]))]
    done = 0
    for _ in range(iterations):
        for x in range(img.width):
            for y in range(img.height):
                if y % 100 == 0:
                    print(f'\r{round((x * img.height + y) / (img.width * img.height) * 100 / iterations+done*100, 3)}%',
                          end='')
                for i in range(len(img_load[x, y])):
                    quads[i].put_pixel(Vector((x, y)), ByteInt(img_load[x, y][i]))
        done += 1/iterations
    print('\r', ' ' * 1000, end='')
    return quads


def dequadify(quads: list[Quad]):
    img = Image.new('RGB', tuple(quads[0].size))
    for x in range(img.width):
        for y in range(img.height):
            if y % 100 == 0:
                print(f'\r{round((x * img.height + y) / (img.width * img.height) * 100, 3)}%', end='')
            color = tuple((quad.get_value_at(Vector((x, y))) for quad in quads))
            img.putpixel((x, y), color)
    return img


def debug_fill_quad(quad: Quad):
    if quad.is_subdivided():
        debug_fill_quads(quad.value)
    else:
        quad.value = tuple([ByteInt(random.randint(0, 255))])
    return quad


def debug_fill_quads(quads: list[Quad] | tuple[Quad]):
    for quad in quads:
        debug_fill_quad(quad)
    return quads


def save_image_as_quads(path: os.PathLike | str, img: Image.Image, margin=25):
    extension = path.split('.')[-1]
    assert extension in ('quads', 'dquads')
    with open(path, 'wb') as f:
        size = str(img.size).encode()
        f.write(str(len(size)).zfill(4).encode() + size)
        loaded_img = img.load()
        quads = [
            Quad(margin=margin).feed_image(loaded_img, img.size, channel=0),
            Quad(margin=margin).feed_image(loaded_img, img.size, channel=1),
            Quad(margin=margin).feed_image(loaded_img, img.size, channel=2),
        ]
        for quad in quads:
            match extension:
                case 'quads':
                    bin_quad = quad.to_bin()
            f.write(str(len(bin_quad)).zfill(8).encode() + bin_quad)


def quick_dequadify(quads: list[Quad]):
    img = Image.new('RGB', list(map(int, quads[0].size)))
    pixels_complete = 0
    pixels = img.width * img.height
    for ind, quad in enumerate(quads[:3]):
        quad_queue = [quad]
        while quad_queue:
            current = quad_queue.pop()
            if current.is_subdivided():
                quad_queue += current.value
            else:
                for x in range(int(current.pos[0]), int(current.pos[0] + current.size[0])):
                    for y in range(int(current.pos[1]), int(current.pos[1] + current.size[1])):
                        val = list(img.getpixel((x, y)))
                        val[ind] = current.value[0]
                        img.putpixel((x, y), tuple(val))
                pixels_complete += current.size[0] * current.size[1] / 3
                print(f'\r{round(pixels_complete / pixels * 100, 3)}%', end='')
    return img


def load_quads_image(path: os.PathLike | str):
    sys.setrecursionlimit(100000)
    version = path.split('.')[-1]
    with open(path, 'rb') as f:
        data = memoryview(f.read())
        size_length = int(data[:4])
        size = tuple(map(int, data[5:4 + size_length - 1].tobytes().decode().split(', ')))
        quads = []
        data = data[size_length + 4:]
        while data:
            quad_size = int(data[:8])
            quad = Quad.from_bytes(data[8:8 + quad_size], Vector(size))
            quads.append(quad)
            data = data[quad_size + 8:]
        img = quick_dequadify(quads)
        img2 = quick_dequadify(debug_fill_quads(quads))
        return img, img2


if __name__ == '__main__':
    image = Image.open('test_squares/test_squares3.png')
    save_image_as_quads('test_squares.quads', image, margin=15)
    print('saved!')
    out1, out2 = load_quads_image('test_squares.quads')
    out1.show()
    out2.show()
