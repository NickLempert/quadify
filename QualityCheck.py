from PIL import Image
from Quadify import load_quads_image
from Vector import Vector


def quality_check(original: Image, new: Image):
    error = 0
    count = 0
    for x in range(0, original.width):
        for y in range(0, original.height):
            error += (sum(Vector((new.getpixel((x, y))))*Vector((0.3, 0.59, 0.11))) - sum(Vector(original.getpixel((x, y)))*Vector((0.3, 0.59, 0.11))))**2
            count += 1
    return error/count


if __name__ == '__main__':
    img = Image.open('[...].png')
    img2 = load_quads_image('[...].quads')[0]
    print()
    print(quality_check(img, img2))
    img2 = load_quads_image('[...].quads')[0]
    print()
    print(quality_check(img, img2))
    img2 = Image.open('[...].jpg')
    print()
    print(quality_check(img, img2))
