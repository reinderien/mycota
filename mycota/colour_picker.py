import typing

import numpy as np
import scipy.optimize
import scipy.sparse
from matplotlib import pyplot as plt
from matplotlib.collections import TriMesh
from matplotlib.tri import Triangulation
from mpl_toolkits.mplot3d import Axes3D


def dict_to_array(colours: dict[str, bytes]) -> np.ndarray:
    """
    Given a dictionary name of friendly names to three-element byte strings,
    return an n*3 ndarray."""
    return np.array(
        [tuple(triple) for triple in colours.values()],
        dtype=np.uint8,
    )


def triples_to_hex(triples: typing.Collection[tuple[int, int, int]]) -> tuple[str, ...]:
    """
    Given a triple iterable (typically an n*3 ndarray of uint8), render a tuple
    of HTML-like colour strings for matplotlib.
    """
    return tuple(
        f'#{red:02x}{green:02x}{blue:02x}'
        for red, green, blue in triples
    )


def fit_plane(colours: np.ndarray) -> tuple[np.ndarray, float]:
    """
    Linear (planar) fit to form (rgb + offset)@abc = rhs. For reasons that I have
    not chased down, this works poorly unless only a subset of points are used for
    the fit.
    """
    offset = -128.  # offset to add to the input; otherwise input (0,0,0) is a problem
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

    print(f'Colour plane of best fit on {len(sel)} colours: (r g b)@{normal} ~ {rhs:.4f}')
    return normal, rhs


def get_corner_idx(
    colour_names: typing.Collection[str],    # all friendly names
    p00: str, p01: str, p10: str, p11: str,  # friendly names for each corner
):
    """Given a collection of colour friendly names and four corner names,
     return array of corresponding indices."""
    corner_names = (p00, p01, p10, p11)
    name_to_index = dict(zip(colour_names, range(len(colour_names))))
    return np.array([name_to_index[k] for k in corner_names])


def fit_project_linprog(
    colours: np.ndarray,         # n*3 rgb colours
    corner_targets: np.ndarray,  # u,v coordinates of coordinate system target corners
    corner_idx: np.ndarray,      # indices of the colour corners
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

    n = len(colours)
    directions = 1 - 2*corner_targets.T  # cost coefficients, 1 or -1

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
    projection_constraint = scipy.optimize.LinearConstraint(A=a, lb=0, ub=0)

    result = scipy.optimize.milp(
        c=cost, integrality=0, bounds=scipy.optimize.Bounds(lb=lb, ub=ub),
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
    the original (rgb) coordinate space on the plane. Because two channels are grid-generated
    and one channel is calculated from the other two, the dtype is float64."""
    channel = np.arange(0, 256, 5, dtype=np.uint8)  # max 255
    ggbb = np.stack(np.meshgrid(channel, channel), axis=-1)
    # For an established green-blue grid, solve for red from the plane equation
    rr = rhs/normal[0] - ggbb@(normal[1:]/normal[0])
    projected = np.concatenate(
        (rr[..., np.newaxis], ggbb), axis=2,
    ).clip(min=0, max=255)
    return projected


def project_irregular(colours: np.ndarray, normal: np.ndarray, rhs: float) -> np.ndarray:
    """Given an n*3 colour matrix, a 3-normal and a planar right-hand side scalar,
    return the colours projected onto the plane, still in rgb space."""
    offset = rhs/normal[0], 0, 0
    v = colours - offset
    w = normal
    return offset + v - np.outer(v@w, w/w.dot(w))


def get_antiprojection(
    colours: np.ndarray,     # original rgb, n*3
    projected: np.ndarray,   # projected uv points, n*2
    corner_idx: np.ndarray,  # indices of corners in colour array
) -> np.ndarray:
    """Calculate an antiprojection matrix from original and projected points."""
    anti, residual, rank, singular = np.linalg.lstsq(
        a=np.hstack((
            projected[corner_idx], np.ones((len(corner_idx), 1)),
        )),
        b=colours[corner_idx],
    )
    print('Antiprojection:')
    print(anti)
    return anti


def plot_2d(
    colours: np.ndarray,    # n*3 array of uint8
    projected: np.ndarray,  # n*3 array of float64, projection to plane of best fit
    rgb_grid: np.ndarray,   # m*m*3 array of float64, projected grid to plane of best fit
    colour_strs: typing.Sequence[str],  # HTML-like codes for original colours
    proj_strs: typing.Sequence[str],    # HTML-like codes for projected colours
) -> plt.Axes:
    """Plot two locii: the original rgb `colours` and the `projected` colours
    on the plane of best fit. The 2D plot projection is not the projection of
    best fit, but the green-blue plane. The original colours are not outlined.
    The projected colours get thin black outlines because otherwise they would
    not be visible against the rendered projection plane."""
    ax: plt.Axes
    fig, ax = plt.subplots()
    rgb = rgb_grid.astype(np.uint8)
    ax.imshow(rgb, extent=(0, 255, 0, 255), origin='lower')
    ax.scatter(colours[:, 1], colours[:, 2], c=colour_strs, label='original')
    ax.scatter(
        projected[:, 1], projected[:, 2], c=proj_strs, label='projected',
        edgecolors='black', linewidths=0.3,
    )
    ax.set_title('RGB coordinate system, plane of best fit')
    ax.set_xlabel('green')
    ax.set_ylabel('blue')
    leg = ax.legend()
    handles: list[plt.PathCollection] = leg.legend_handles
    handles[0].set_facecolor('orange')
    handles[1].set_facecolor('orange')
    return ax


def plot_3d(
    colours: np.ndarray,    # n*3 array of uint8
    projected: np.ndarray,  # n*3 array of float64, projection to plane of best fit
    colour_names: typing.Collection[str],  # friendly colour names
    colour_strs: typing.Sequence[str],  # HTML-like codes for original colours
    proj_strs: typing.Sequence[str],    # HTML-like codes for projected colours
) -> Axes3D:
    """Plot two locii: the original rgb `colours` and the `projected` colours
    on the plane of best fit. Unlike in the 2D case, the plane itself is not rendered."""
    fig, ax = plt.subplots(subplot_kw={'projection': '3d'})
    ax: Axes3D
    ax.scatter3D(*colours.T, c=colour_strs, depthshade=False)
    ax.scatter3D(*projected.T, c=proj_strs, depthshade=False)
    for name, pos in zip(colour_names, colours):
        ax.text(*pos, name)
    ax.set_title('Projection to plane of best fit')
    ax.set_xlabel('red')
    ax.set_ylabel('green')
    ax.set_zlabel('blue')
    return ax


def plot_correspondences(
    ax2: plt.Axes,  # 2D axes (green-blue projection)
    ax3: Axes3D,    # RGB axes
    colours: np.ndarray,    # n*3 array of uint8
    projected: np.ndarray,  # n*3 array of float64, projection to plane of best fit
) -> None:
    """For both 2D and 3D axes, plot lines between original and projected points"""
    for orig, proj in zip(colours, projected):
        ax2.plot(
            [orig[1], proj[1]], [orig[2], proj[2]],
            c='black',
        )
        ax3.plot(
            [orig[0], proj[0]], [orig[1], proj[1]], [orig[2], proj[2]],
            c='black',
        )


def plot_labels(
    ax: plt.Axes,           # to plot on
    colours: np.ndarray,    # n*3 array of uint8
    projected: np.ndarray,  # n*2 uv projected colours
    names: typing.Collection[str],  # friendly colour names
)-> None:
    for name, pos, colour in zip(names, projected, colours):
        c = 'lightgrey' if np.linalg.norm(colour) < 160 else 'black'
        ax.text(*pos, name, c=c, rotation=30)


def plot_reduction_planar(
    colours: np.ndarray,  # n*3 array of uint8
    colour_names: typing.Collection[str],  # friendly colour names
    colour_strs: typing.Sequence[str],     # HTML-like codes for original colours
    antiprojection: np.ndarray,  # 3x3 uv1->rgb
    projected: np.ndarray,       # n*2 uv projected colours
) -> plt.Axes:
    """Plot points projected into u,v space."""
    fig, ax = plt.subplots()

    uv_series = np.linspace(start=0, stop=1, num=21)
    uv_homogeneous = np.stack(
        np.meshgrid(uv_series, uv_series) +
        (np.ones((uv_series.size, uv_series.size)),),
        axis=2,
    )
    rgb = (
        (uv_homogeneous @ antiprojection)
        .clip(min=0, max=255).round()
        .astype(np.uint8)
    )
    ax.imshow(rgb, extent=(0, 1, 0, 1), origin='lower')
    ax.scatter(
        projected[:, 0],
        projected[:, 1],
        c=colour_strs,
    )
    fig.suptitle('Planar reduction')
    ax.set_xlabel('u')
    ax.set_ylabel('v')
    plot_labels(ax=ax, colours=colours, projected=projected, names=colour_names)
    return ax


def plot_delaunay_gouraud(
    colours: np.ndarray,  # n*3 array of uint8
    colour_names: typing.Collection[str],  # friendly colour names
    colour_strs: typing.Sequence[str],     # HTML-like codes for original colours
    corner_targets: np.ndarray,  # uv coordinates of the coordinate space corners
    antiprojection: np.ndarray,  # 3x3 uv1->rgb
    projected: np.ndarray,       # n*2 uv projected colours
) -> plt.Axes:
    """Plot projected points in uv space using Delaunay triangulation and Gouraud shading. The uv
    'target' corners (to which, sometimes, no named colour has been mapped) are extrapolated."""
    fig, ax = plt.subplots()
    missing_corners = corner_targets[~(
        projected[np.newaxis, ::] == corner_targets[:, np.newaxis, :]
    ).all(axis=2).any(axis=1)]
    projected_with_corners = np.concatenate((projected, missing_corners), axis=0)

    corner_rgb = (
        np.hstack((missing_corners, np.ones((len(missing_corners), 1)))) @ antiprojection
    ).clip(min=0, max=255).astype(np.uint8)
    all_strs = colour_strs + triples_to_hex(corner_rgb)

    delaunay = Triangulation(*projected_with_corners.T)
    mesh = TriMesh(triangulation=delaunay, color=all_strs)
    ax.add_collection(mesh)

    plot_labels(ax=ax, colours=colours, projected=projected, names=colour_names)

    fig.suptitle('Delaunay-Gouraud interpolation')
    ax.set_xlabel('u')
    ax.set_ylabel('v')

    return ax


def demo_planar(
    colours: np.ndarray,  # n*3 array of uint8
    colour_names: typing.Collection[str],  # friendly colour names
    colour_strs: typing.Sequence[str],     # HTML-like codes for colours
) -> None:
    """Calculate and plot a simple linear regression. Doesn't work very well, but it's useful to
    look at the RGB points in 3D."""

    normal, rhs = fit_plane(colours=colours)
    rgb_float = project_grid(normal=normal, rhs=rhs)
    projected = project_irregular(colours=colours, normal=normal, rhs=rhs)
    proj_strs = triples_to_hex(triples=projected.clip(min=0, max=255).astype(np.uint8))

    ax2 = plot_2d(colours=colours, projected=projected, rgb_grid=rgb_float,
                  colour_strs=colour_strs, proj_strs=proj_strs)
    ax3 = plot_3d(colours=colours, projected=projected, colour_names=colour_names,
                  colour_strs=colour_strs, proj_strs=proj_strs)
    plot_correspondences(ax2=ax2, ax3=ax3, colours=colours, projected=projected)


def demo_reduction(
    colours: np.ndarray,  # n*3 array of uint8
    colour_names: typing.Collection[str],  # friendly colour names
    colour_strs: typing.Sequence[str],     # HTML-like codes for colours
) -> None:
    """Calculate a reducing projection from rgb->uv using linear programming, and plot. This is what
    we'll probably use as the basis for a colour picker in a UI."""

    # Also possible: black, purple, yellow-orange, white
    corner_idx = get_corner_idx(
        colour_names=colour_names,
        p00='black', p01='green', p10='ochre', p11='white',
    )
    corner_targets = np.array(((0, 0), (0, 1), (1, 0), (1, 1)))

    projection, projected = fit_project_linprog(
        colours=colours, corner_idx=corner_idx, corner_targets=corner_targets,
    )
    antiprojection = get_antiprojection(
        colours=colours, corner_idx=corner_idx, projected=projected,
    )
    plot_reduction_planar(
        colours=colours, colour_names=colour_names, colour_strs=colour_strs,
        projected=projected, antiprojection=antiprojection,
    )
    plot_delaunay_gouraud(
        colours=colours, colour_names=colour_names, colour_strs=colour_strs,
        projected=projected, antiprojection=antiprojection, corner_targets=corner_targets,
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
    colour_names = colour_dict.keys()
    colours = dict_to_array(colour_dict)
    colour_strs = triples_to_hex(triples=colour_dict.values())

    if lp_reduction:
        demo_reduction(colour_names=colour_names, colours=colours, colour_strs=colour_strs)
    else:
        demo_planar(colour_names=colour_names, colours=colours, colour_strs=colour_strs)

    plt.show()


demo(True)
