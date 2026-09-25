from __future__ import annotations

import os
import random
import sys
import time

from PIL import Image
from typing import ByteString, Iterable

from Vector import Vector


def pop_bit(string: str):
    bit, rest = ord(string[0]) % 2, \
                ''.join((chr(ord(string[i + 1]) % 2 * 128 + ord(string[i]) // 2)) for i in range(len(string) - 1)) \
                + chr(ord(string[-1]) // 2)
    return bit, rest


def push_bit(bit: int, string: str):
    # return chr((ord(string[0])*2+bit) % 256)\
    #        + ''.join((chr(ord(string[i-1]) * 2 % 256 + ord(string[i]) * 2)) for i in range(1, len(string)))
    num = ((ord(string[0]) * 2) + bit)
    new_string = chr(num % 256)
    carry = num // 256
    string = string[1:]
    while string:
        num = ((ord(string[0]) * 2) + carry)
        new_string += chr(num % 256)
        carry = num // 256
        string = string[1:]
    while carry:
        new_string += chr(carry % 256)
        carry //= 256
    return new_string


class Binable:
    def to_bin(self) -> bytes:
        return b''


def to_bin(binable: Binable | int):
    return binable.to_bin()


def to_bin_dense(binable: Binable):
    if isinstance(binable, Quad):
        return binable.to_bin_dense()
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
        return chr(int(self)).encode()

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

    def put_pixel(self, at_pos: Vector[float, float], value: ByteInt):
        self.used += 1
        if self.used <= 1:
            self.value = [value]
            return
        if not self.is_subdivided():
            if abs(self.get_value() - value) > self.margin:
                self.subdivide()
                self.put_pixel(at_pos, value)
            else:
                # self.value = [ByteInt(((self.size[0]*self.size[1]-1)*int(self.get_value())+int(value))
                #               // (self.size[0]*self.size[1]))]
                self.value = [ByteInt(((self.used - 1) * int(self.get_value()) + int(value))
                                      // self.used)]
        else:
            for quad in self.value:
                if isinstance(quad, Quad):  # for the IDE
                    if quad.includes(at_pos):
                        quad.put_pixel(at_pos, value)

    def to_bin(self):
        return chr(int(self.is_subdivided())).encode() + b''.join(map(to_bin, reversed(self.value)))

    def to_bin_dense(self):
        return push_bit(int(self.is_subdivided()),
                        b''.join(map(to_bin_dense, reversed(self.value))).decode()).encode()

    def get_value_at(self, pos: Vector[float, float]):
        if self.is_subdivided():
            for quad in self.value:
                if quad.includes(pos):
                    return quad.get_value_at(pos)
        return int(self.get_value())

    @staticmethod
    def from_string(string, size: Vector[float, float] = None) -> Quad:
        quad = Quad(size=size)
        quad_stack = [quad]
        # print(string)
        while quad_stack and string != '':
            # print(ord(string[0]), string[0])
            operating_quad = quad_stack.pop(-1)
            if ord(string[0]) == 1:
                quad_stack += operating_quad.subdivide()
                string = string[1:]
            else:
                operating_quad.value = [ByteInt(ord(string[1]))]
                string = string[2:]
        # print(quad.to_bin().decode())
        return quad

    @staticmethod
    def from_dense_string(string, size: Vector[float, float] = None) -> Quad:
        quad = Quad(size=size)
        quad_stack = [quad]
        start_length = len(string)
        while quad_stack and string != '':
            print(f'\r{len(string)} {100-round(len(string) / start_length * 100, 3)}%', end='')
            operating_quad = quad_stack.pop(-1)
            bit, string = pop_bit(string)
            if bit == 1:
                quad_stack += operating_quad.subdivide()
            else:
                operating_quad.value = [ByteInt(ord(string[0]))]
                string = string[1:]
        if string != '':
            print('something went wrong!')
        print()
        return quad


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
    assert path.split('.')[-1] in ('quads', 'dquads')
    with open(path, 'wb') as f:
        size = str(img.size).encode()
        f.write(str(len(size)).zfill(4).encode() + size)
        quads = quadify_image(img, margin=margin)
        for quad in quads:
            if path.split('.')[1] == 'dquads':
                bin_quad = quad.to_bin_dense()
            else:
                bin_quad = quad.to_bin()
            f.write(str(len(bin_quad.decode())).zfill(8).encode() + bin_quad)


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
    old_quads = path.split('.')[-1] == 'quads'
    with open(path, 'rb') as f:
        data = f.read().decode()
        size_length = int(data[:4])
        size = tuple(map(int, data[5:4 + size_length - 1].split(', ')))
        quads = []
        data = data[size_length + 4:]
        while data:
            quad_size = int(data[:8])
            if old_quads:
                quad = Quad.from_string(data[8:8 + quad_size], Vector(size))
            else:
                quad = Quad.from_dense_string(data[8:8 + quad_size], Vector(size))
            quads.append(quad)
            data = data[quad_size + 8:]
        img = quick_dequadify(quads)
        img2 = quick_dequadify(debug_fill_quads(quads))
        return img, img2


if __name__ == '__main__':

    s = 'hello world!'
    s2 = ''.join((push_bit(i % 2, s[i]) for i in range(len(s))))
    print(' '.join(s2))
    print(*map(lambda x: pop_bit(x)[0], s2))
    print(*map(lambda x: pop_bit(x)[1], s2))
    for _ in range(8*6):
        bit2, s = pop_bit(s)
        print(bit2, end='')
    print()
    for i in s:
        print(ord(i))
    print(s)

    image = Image.open('images/test_squares/test_squares2.png')
    # quadified = quadify_image(image)
    # print(*map(to_bin, quadified))
    # dequadify(quadified).show()
    # dequadify(debug_fill_quads(quadified)).show()

    # save_image_as_quads('test_squares.dquads', image, margin=25)
    save_image_as_quads('test_squares.dquads', image, margin=5)
    print('saved!')
    out1, out2 = load_quads_image('test_squares.dquads')
    out1.show()
    out2.show()
