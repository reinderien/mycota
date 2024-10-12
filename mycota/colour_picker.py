import typing

import numpy as np
import scipy.sparse
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.optimize import milp, Bounds, LinearConstraint


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


def fit_matrix_from_map(
    colour_dict: dict[str, bytes], colours: np.ndarray,
    mapping: dict[str, tuple[float, float]],
) -> np.ndarray:
    name_to_index = dict(zip(colour_dict.keys(), range(len(colour_dict))))
    a = np.hstack((  # 4*4
        np.array([
            colours[name_to_index[k]]
            for k in mapping.keys()
        ]),
        np.ones((len(mapping), 1)),
    ))
    # x is 4*2
    b = np.array(tuple(mapping.values()))
    projection, residual, rank, singular = np.linalg.lstsq(a, b, rcond=None)
    if rank != 4:
        raise ValueError(f'Deficient rank {rank}')
    return projection


def fit_matrix_linprog(
    colour_dict: dict[str, bytes], colours: np.ndarray,
    p00: str, p01: str, p10: str, p11: str,
) -> np.ndarray:
    name_to_index = dict(zip(colour_dict.keys(), range(len(colour_dict))))

    places = ((0,0), (0,1), (1,0), (1,1))
    corner_names = (p00, p01, p10, p11)
    directions = [
        1 - 2*i
        for axis in zip(*places)
        for i in axis
    ]
    corner_set = frozenset(corner_names)

    corner_idx = [name_to_index[k] for k in corner_names]
    corner_rgb = colours[corner_idx, :]
    off_corner_rgb = np.array([
        colours[i]
        for k, i in name_to_index.items()
        if k not in corner_set
    ])

    '''
    variables:
    a e
    b f
    c g
    d h
    and xy for each of corners "p"
    flattened as:
    abcd efgh x00 01 10 11 y00 01 10 11

    objective:
        minimize ap00x + bp00y + cp00z + d
        minimize ep00x + fp00y + gp00z + h
        minimize ap01x + bp01y + cp01z + d
        maximize ep01x + fp01y + gp01z + h
        maximize ap10x + bp10y + cp10z + d
        minimize ep10x + fp10y + gp10z + h
        maximize ap11x + bp11y + cp11z + d
        maximize ep11x + fp11y + gp11z + h

    constraints:
        relate ah and p
        every colour projected must be between 0 and 1
    '''

    # rgb1 0000 -1 000 0000 = 0
    # rgb1 0000  0-100 0000 = 0
    # ...
    affine = np.hstack((corner_rgb, np.ones((len(corner_idx), 1))))
    a = scipy.sparse.hstack((
        scipy.sparse.block_diag((affine, affine), format='bsr'),
        -scipy.sparse.eye_array(m=2*len(corner_idx), format='dia'),
    ), format='csc')
    corner_constraint = LinearConstraint(A=a, lb=0, ub=0)

    # 0 <= rgb1 0000 00000000 <= 1
    # ...
    # 0 <= 0000 rgb1 00000000 <= 1
    affine = np.hstack((off_corner_rgb, np.ones((len(off_corner_rgb), 1))))
    a = scipy.sparse.block_diag((affine, affine), format='csc')
    a.resize((a.shape[0], 2*(4 + len(corner_idx))))
    off_corner_constraint = LinearConstraint(A=a, lb=0, ub=1)

    result = milp(
        # a-h     px, py
        c=[0]*8 + directions,
        integrality=0,
        bounds=Bounds(
            #   a-h           pxy
            lb=(-np.inf,)*8 + (0,)*(2*len(corner_idx)),
            ub=(+np.inf,)*8 + (1,)*(2*len(corner_idx)),
        ),
        constraints=(corner_constraint, off_corner_constraint),
    )
    if not result.success:
        raise ValueError(result.message)
    projection, corners = np.split(result.x, (8,))
    return projection.reshape((2, -1)).T


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


def project_reduction(colours: np.ndarray, projection: np.ndarray) -> np.ndarray:
    return np.hstack((
        colours, np.ones((len(colours), 1)),
    )) @ projection


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
    colours: np.ndarray, projected: np.ndarray, colour_dict: dict[str, bytes],
    colour_strs: tuple[str, ...], proj_strs: tuple[str, ...],
) -> Axes3D:
    fig, ax = plt.subplots(subplot_kw={'projection': '3d'})
    ax: Axes3D
    ax.scatter3D(*colours.T, c=colour_strs, depthshade=False)
    ax.scatter3D(*projected.T, c=proj_strs, depthshade=False)
    for name, pos in zip(colour_dict.keys(), colours):
        ax.text(*pos, name)
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


def plot_reduction_planar(
    colour_dict: dict[str, bytes],
    colour_strs: typing.Sequence[str],
    projection: np.ndarray,
    projected: np.ndarray,
) -> plt.Axes:
    fig, ax = plt.subplots()

    '''
    Solve backward for colour plane:
    If 
    [rgb1] [ae] = [uv]
    [rgb1] [bf]   [uv]
    [rgb1] [cg]   [uv]
    [rgb1] [dh]   [uv]
    [rgb1]        [uv]
    [rgb1]        [uv]
    and abcdefgh and uv are known,
    [abcd][rrrrrrr] = [uuuuuuu]
    [efgh][ggggggg]   [vvvvvvv]
          [bbbbbbb]
          [1111111]
    '''
    uv_series = np.linspace(start=0, stop=1, num=11)
    uv = np.stack(
        np.meshgrid(uv_series, uv_series),
        axis=0,
    )
    deprojected, residuals, rank, singular = np.linalg.lstsq(
        a=projection.T, b=uv.reshape((2, -1)), rcond=None,
    )
    if rank != 2:
        raise ValueError(f'Deficient rank {rank}')
    rgb = (
        deprojected[:3]
        .clip(min=0, max=255).round()
        .astype(np.uint8)
        .T.reshape(uv.shape[1:] + (3,))
    )

    ax.imshow(rgb, extent=(0, 1, 0, 1), origin='lower')
    ax.scatter(
        projected[:, 0],
        projected[:, 1],
        c=colour_strs,
    )
    for name, pos in zip(colour_dict.keys(), projected):
        ax.text(*pos, name)
    return ax


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
    colour_strs = triples_to_hex(triples=colour_dict.values())
    projection = fit_matrix_linprog(
        colour_dict=colour_dict, colours=colours,
        p00='black',
        p01='purple',
        p10='yellow-orange',
        p11='white',
    )
    projected = project_reduction(colours=colours, projection=projection)
    plot_reduction_planar(
        colour_dict=colour_dict, colour_strs=colour_strs,
        projection=projection, projected=projected,
    )

    plt.show()


demo()
