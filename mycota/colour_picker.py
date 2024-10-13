import typing

import numpy as np
import scipy.sparse
from matplotlib import pyplot as plt
from matplotlib.collections import TriMesh
from matplotlib.tri import Triangulation
from mpl_toolkits.mplot3d import Axes3D
from scipy.optimize import milp, Bounds, LinearConstraint


def dict_to_array(colours: dict[str, bytes]) -> np.ndarray:
    """
    Given a dictionary name of friendly names to three-element byte strings,
    return an n*3 ndarray. Because this is intended for processing, the dtype is
    float64 and not uint8."""
    return np.array([tuple(triple) for triple in colours.values()])


def triples_to_hex(triples: typing.Iterable[tuple[int, int, int]]) -> tuple[str, ...]:
    """
    Given a triple iterable (typically an ndarray of dtype uint), render a tuple
    of HTML-like colour strings for matplotlib.
    """
    return tuple(
        f'#{red:02x}{green:02x}{blue:02x}'
        for red, green, blue in triples
    )


def fit_plane(
    colours: np.ndarray,
) -> tuple[np.ndarray, float]:
    """
    Linear (planar) fit to form (rgb + offset)@abc = rhs. For reasons that I have
    not chased down, this works poorly unless only a subset of points are used for
    the fit.
    """
    offset = -128  # offset to add to the input; otherwise input (0,0,0) is a problem
    rhs = 127
    sel = [0, 6, 12, 18, -1]  # selected indices of points for fit
    normal, residuals, rank, singular = np.linalg.lstsq(
        a=colours[sel] + offset, b=np.full(shape=len(sel), fill_value=rhs),
        rcond=None,
    )
    if rank != 3:
        raise ValueError(f'Deficient rank {rank}')

    # Account for offset: (rgb + offset)@norm = rhs
    # rgb@norm = 255 - offset*norm.sum()
    rhs -= offset*normal.sum()

    mag = np.linalg.norm(normal)
    normal /= mag   # normalise
    rhs /= mag

    print(f'Colour plane of best fit: (r g b)@{normal} ~ {rhs}')
    return normal, rhs


def fit_project_linprog(
    colour_dict: dict[str, bytes], colours: np.ndarray,
    p00: str, p01: str, p10: str, p11: str,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Given the name-colourbytes dictionary, the n*3 colour matrix, and four corner
    colour names, create a projection using a linear program. The projection has
    the following characteristics:

    - It's a 4*2 affine homogeneous matrix (though typically the last row evaluates to 0)
    - It projects rgb space to uv space
    - All projected uv coordinates lie in [0, 1]
    - The four named corner colours are pulled as far as possible to the corners of the uv
      coordinate space.

    The projection matrix (4*2) and the projected colour point matrix (n*2) are returned.
    """

    n = len(colour_dict)
    corner_targets = np.array(((0,0), (0,1), (1,0), (1,1),))
    corner_names = (p00, p01, p10, p11)
    directions = 1 - 2*corner_targets.T  # cost coefficients, 1 or -1
    name_to_index = dict(zip(colour_dict.keys(), range(len(colour_dict))))
    corner_idx = np.array([name_to_index[k] for k in corner_names])

    '''
    Linear program variables:
    a e    # projection
    b f
    c g
    d h,
    u,     # projected coordinates
    v;    
    flattened as:
    abcd efgh uuuuuu... vvvvvv...

    objective:
        minimize all corner u, v for which target=0
        maximize all corner u, v for which target=1

    constraints:
        rgb@proj == uv
        
    bounds:
        0 <= uv <= 1
    '''

    cost = np.zeros(2*4 + 2*n)
    cost[2*4 + corner_idx] = directions[0]
    cost[2*4 + corner_idx + n] = directions[1]

    lb = np.concatenate((
        np.full(shape=2*4, fill_value=-np.inf),  # projection
        np.zeros(shape=2*n),                     # projected uv
    ))
    ub = np.concatenate((
        np.full(shape=2*4, fill_value=+np.inf),  # projection
        np.ones(shape=2*n),                      # projected uv
    ))

    # The projection must exactly produce the projected points
    # rgb1 0000 -1000  0000 = 0 ...
    # 0000 rgb1  0000 -1000 = 0 ...
    affine = np.hstack((colours, np.ones((n, 1))))
    a = scipy.sparse.hstack((
        scipy.sparse.block_diag((affine, affine), format='bsr'),
        -scipy.sparse.eye_array(m=2*n, format='dia'),
    ), format='csc')
    projection_constraint = LinearConstraint(A=a, lb=0, ub=0)

    result = milp(
        c=cost, integrality=0, bounds=Bounds(lb=lb, ub=ub),
        constraints=projection_constraint,
    )
    if not result.success:
        raise ValueError(result.message)
    projection, projected = np.split(result.x, (2*4,))
    projection = projection.reshape((2, 4)).T
    projected = projected.reshape((2, -1)).T
    print('Projection:')
    print(projection)
    print('Projected corners:')
    print(projected[corner_idx])
    return projection, projected


def project_grid(normal: np.ndarray, rhs: float) -> np.ndarray:
    """Given a planar normal and equation right-hand side, generate a grid in
    the original (rgb) coordinate space on the plane."""
    channel = np.linspace(start=0, stop=255, num=40)
    ggbb = np.stack(np.meshgrid(channel, channel), axis=-1)
    # For an established green-blue grid, solve for red from the plane equation
    rr = rhs/normal[0] - ggbb@(normal[1:]/normal[0])
    return np.concatenate(
        (rr[..., np.newaxis], ggbb), axis=2,
    ).clip(min=0, max=255)


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


def plot_delaunay_gouraud(
    colours: np.ndarray,
    colour_dict: dict[str, bytes],
    colour_strs: typing.Sequence[str],
    projected: np.ndarray,
) -> plt.Axes:
    fig, ax = plt.subplots()
    delaunay = Triangulation(*projected.T)
    mesh = TriMesh(triangulation=delaunay, color=colour_strs)
    ax.add_collection(mesh)

    for name, pos, colour in zip(colour_dict.keys(), projected, colours):
        c = 'lightgrey' if np.linalg.norm(colour) < 160 else 'black'
        ax.text(*pos, name, c=c, rotation=30)

    return ax


def demo_planar(
    colour_dict: dict[str, bytes],
    colours: np.ndarray,
    colour_strs: typing.Sequence[str],
) -> None:
    normal, rhs = fit_plane(colours=colours)
    rgb_float = project_grid(normal=normal, rhs=rhs)
    projected = project_irregular(colours=colours, normal=normal, rhs=rhs)
    proj_strs = triples_to_hex(triples=projected.clip(min=0, max=255).astype(np.uint8))

    ax2 = plot_2d(colours=colours, projected=projected, rgb_grid=rgb_float,
                  colour_strs=colour_strs, proj_strs=proj_strs)
    ax3 = plot_3d(colours=colours, projected=projected, colour_dict=colour_dict,
                  colour_strs=colour_strs, proj_strs=proj_strs)
    plot_correspondences(ax2=ax2, ax3=ax3, colours=colours, projected=projected)


def demo_reduction(
    colour_dict: dict[str, bytes],
    colours: np.ndarray,
    colour_strs: typing.Sequence[str],
) -> None:
    # Also possible: black, purple, yellow-orange, white
    projection, projected = fit_project_linprog(
        colour_dict=colour_dict, colours=colours,
        p00='black', p01='green', p10='ochre', p11='white',
    )
    plot_delaunay_gouraud(
        colours=colours, colour_dict=colour_dict, colour_strs=colour_strs,
        projected=projected,
    )


def demo(lp_reduction: bool = True) -> None:
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

    if lp_reduction:
        demo_reduction(colour_dict=colour_dict, colours=colours, colour_strs=colour_strs)
    else:
        demo_planar(colour_dict=colour_dict, colours=colours, colour_strs=colour_strs)

    plt.show()


demo(False)
