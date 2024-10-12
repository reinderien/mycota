import typing

import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def dict_to_array(colours: dict[str, bytes]) -> np.ndarray:
    return np.array([tuple(triple) for triple in colours.values()])


def triples_to_hex(triples: typing.Iterable[tuple[int, int, int]]) -> tuple[str, ...]:
    return tuple(
        f'#{red:02x}{green:02x}{blue:02x}'
        for red, green, blue in triples
    )


def fit_plane(
    colours: np.ndarray,
) -> tuple[np.ndarray, float]:
    offset = -128
    rhs = 255
    # Plane of best fit to form ax + by + cz + 256 = 255
    sel = [0, 6, 12, 18, -1]
    normal, residuals, rank, singular = np.linalg.lstsq(
        a=colours[sel] + offset,
        b=np.full(shape=len(sel), fill_value=rhs),
        rcond=None,
    )
    if rank != 3:
        raise ValueError(f'Deficient rank {rank}')

    # (rgb + offset)@norm = 255
    # rgb@norm = 255 - offset*norm.sum()
    rhs -= offset*normal.sum()
    print(f'Colour plane of best fit: (r g b) .', normal, '~', rhs)
    return normal, rhs


def project_grid(normal: np.ndarray, rhs: float) -> np.ndarray:
    channel = np.linspace(start=0, stop=255, num=40)
    ggbb = np.stack(
        np.meshgrid(channel, channel), axis=-1,
    )
    rr = rhs/normal[0] - ggbb@(normal[1:]/normal[0])
    rgb = np.concatenate((rr[..., np.newaxis], ggbb), axis=2)
    rgb[(rgb > 255).any(axis=-1)] = np.nan
    return rgb


def project_irregular(colours: np.ndarray, normal: np.ndarray, rhs: float) -> np.ndarray:
    offset = rhs/normal[0], 0, 0
    v = colours - offset
    w = normal
    return offset + v - np.outer(v@w, w/w.dot(w))


def plot_2d(
    colours: np.ndarray, projected: np.ndarray,
    rgb_grid: np.ndarray,
    colour_strs: tuple[str, ...], proj_strs: tuple[str, ...],
) -> plt.Axes:
    ax: plt.Axes
    fig, ax = plt.subplots()
    rgb = np.full_like(rgb_grid, fill_value=100)  # dark grey
    mask = ((rgb_grid >= 0) & (rgb_grid <= 255)).all(axis=-1)
    rgb[mask] = rgb_grid[mask]
    rgb = rgb.astype(np.uint8)
    ax.imshow(rgb, extent=(0, 255, 0, 255), origin='lower')
    ax.scatter(colours[:, 1], colours[:, 2], c=colour_strs)
    ax.scatter(
        projected[:, 1], projected[:, 2], edgecolors='black', linewidths=0.2,
        c=proj_strs,
    )
    ax.set_title('RGB coordinate system, plane of best fit')
    ax.set_xlabel('green')
    ax.set_ylabel('blue')
    return ax


def plot_3d(
    colours: np.ndarray, projected: np.ndarray,
    colour_strs: tuple[str, ...], proj_strs: tuple[str, ...],
) -> Axes3D:
    fig, ax = plt.subplots(subplot_kw={'projection': '3d'})
    ax: Axes3D
    ax.scatter3D(*colours.T, c=colour_strs, depthshade=False)
    ax.scatter3D(*projected.T, c=proj_strs, depthshade=False)
    ax.set_xlabel('red')
    ax.set_ylabel('green')
    ax.set_zlabel('blue')
    return ax


def plot_correspondences(
    ax2: plt.Axes, ax3: Axes3D, colours: np.ndarray, projected: np.ndarray,
) -> None:
    for orig, proj in zip(colours, projected):
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


def demo() -> None:
    # from https://en.wikipedia.org/w/index.php?title=Template:Mycomorphbox&action=edit
    colour_dict = {
        'black': b'\x00\x00\x00',
        'white': b'\xFF\xFF\xFF',
        'olive': b'\x78\x88\x61',
        'olive-brown': b'\x87\x81\x56',
        'brown': b'\x5d\x43\x1f',
        'yellow': b'\xf2\xef\xba',
        'pink': b'\xf7\xcf\xca',
        'tan': b'\xcb\xa7\x77',
        'salmon': b'\xf6\xcf\xb3',
        'ochre': b'\xcc\x77\x22',
        'cream': b'\xfa\xf5\xe7',
        'buff': b'\xeb\xd6\x9a',
        'blackish-brown': b'\x27\x1c\x13',
        'reddish-brown': b'\x67\x32\x1a',
        'pinkish-brown': b'\xf4\xc6\xa6',
        'green': b'\x7c\x8a\x68',
        'yellow-orange': b'\xff\xbf\x68',
        'purple': b'\x5a\x43\x64',
        'purple-black': b'\x3b\x2a\x42',
        'purple-brown': b'\x4b\x35\x45',
        'yellow-brown': b'\xcb\x97\x35',
    }

    colours = dict_to_array(colour_dict)
    normal, rhs = fit_plane(colours=colours)
    rgb_float = project_grid(normal=normal, rhs=rhs)
    projected = project_irregular(colours=colours, normal=normal, rhs=rhs)
    colour_strs = triples_to_hex(triples=colour_dict.values())
    proj_strs = triples_to_hex(triples=projected.clip(min=0, max=255).astype(np.uint8))

    ax2 = plot_2d(colours=colours, projected=projected, rgb_grid=rgb_float,
                  colour_strs=colour_strs, proj_strs=proj_strs)
    ax3 = plot_3d(colours=colours, projected=projected,
                  colour_strs=colour_strs, proj_strs=proj_strs)
    plot_correspondences(ax2=ax2, ax3=ax3, colours=colours, projected=projected)

    plt.show()


demo()
