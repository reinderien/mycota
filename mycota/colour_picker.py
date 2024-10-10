import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from mpl_toolkits.mplot3d import Axes3D

# from https://en.wikipedia.org/w/index.php?title=Template:Mycomorphbox&action=edit
COLOURS = {
    'black':          b'\x00\x00\x00',
    'white':          b'\xFF\xFF\xFF',
    'olive':          b'\x78\x88\x61',
    'olive-brown':    b'\x87\x81\x56',
    'brown':          b'\x5d\x43\x1f',
    'yellow':         b'\xf2\xef\xba',
    'pink':           b'\xf7\xcf\xca',
    'tan':            b'\xcb\xa7\x77',
    'salmon':         b'\xf6\xcf\xb3',
    'ochre':          b'\xcc\x77\x22',
    'cream':          b'\xfa\xf5\xe7',
    'buff':           b'\xeb\xd6\x9a',
    'blackish-brown': b'\x27\x1c\x13',
    'reddish-brown':  b'\x67\x32\x1a',
    'pinkish-brown':  b'\xf4\xc6\xa6',
    'green':          b'\x7c\x8a\x68',
    'yellow-orange':  b'\xff\xbf\x68',
    'purple':         b'\x5a\x43\x64',
    'purple-black':   b'\x3b\x2a\x42',
    'purple-brown':   b'\x4b\x35\x45',
    'yellow-brown':   b'\xcb\x97\x35',
}

colour_array = np.array([tuple(triple) for triple in COLOURS.values()])
colour_strs = [
    f'#{red:02x}{green:02x}{blue:02x}'
    for red, green, blue in COLOURS.values()
]

# Plane of best fit to form ax + by + cz = 255
plane, (residual,), rank, singular = np.linalg.lstsq(
    a=colour_array, b=np.full(len(colour_array), fill_value=255), rcond=None,
)
if rank != 3:
    raise ValueError(f'Deficient rank {rank}')
print('Colour plane of best fit: 255 ~ (r g b) .', plane)

channel = np.linspace(start=0, stop=255, num=40)
ggbb = np.stack(
    np.meshgrid(channel, channel), axis=-1,
)
rr = 255/plane[0] - ggbb@(plane[1:]/plane[0])
rgb_float = np.concatenate((rr[..., np.newaxis], ggbb), axis=2)
rgb_float[(rgb_float > 255).any(axis=-1)] = np.nan

offset = 255/plane[0], 0, 0
v = colour_array - offset
w = plane
projected = offset + v - np.outer(v @ w, w/w.dot(w))

rgb = np.nan_to_num(rgb_float, nan=100).astype(np.uint8)  # dark grey

fig3, ax3 = plt.subplots(subplot_kw={'projection': '3d'})
ax3: Axes3D
ax3.scatter3D(*colour_array.T, c=colour_strs, depthshade=False)
proj_strs = [
    f'#{red:02x}{green:02x}{blue:02x}'
    for red, green, blue in projected.clip(min=0, max=255).astype(np.uint8)
]
ax3.scatter3D(*projected.T, c=proj_strs, depthshade=False)
ax3.set_xlabel('red')
ax3.set_ylabel('green')
ax3.set_zlabel('blue')

fig2, ax2 = plt.subplots()
ax2: Axes
ax2.imshow(rgb, extent=(0, 255, 0, 255), origin='lower')
ax2.scatter(colour_array[:, 1], colour_array[:, 2], c=colour_strs)
ax2.scatter(
    projected[:, 1], projected[:, 2], edgecolors='black', linewidths=0.2,
    c=proj_strs,
)
ax2.set_title('RGB coordinate system, plane of best fit')
ax2.set_xlabel('green')
ax2.set_ylabel('blue')

for orig, proj in zip(colour_array, projected):
    ax2.plot(
        [orig[1], proj[1]], [orig[2], proj[2]],
        c='black',
    )
    ax3.plot(
        [orig[0], proj[0]],
        [orig[1], proj[1]],
        [orig[2], proj[2]],
        c='black',
    )

plt.show()
