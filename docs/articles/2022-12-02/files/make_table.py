import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from scipy.misc import derivative


FUNCTION_COLUMN = 0
DERIVATIVE_COLUMN = 1

MAIN_COLOR = 'xkcd:navy'
SECONDARY_COLOR = 'xkcd:brick red'
FUNCTION_Y_TICKS_COLOR = SECONDARY_COLOR
DERIVATIVE_LINE_COLOR = SECONDARY_COLOR
DERIVATIVE_X_TICKS_COLOR = SECONDARY_COLOR
TITLE_COLOR = ANNOTATION_COLOR = 'xkcd:grey purple'
SECONDARY_LINE_WIDTH = 1
SECONDARY_ALPHA = 0.5
MARGIN_Y = 0.2

ANN_LIN = r'$f(x)$'
ANN_QUAD = r'$f(x^2)$'
ANN_CUB = r'$f(x^3)$'
ANN_EXP = r'$f(e^x)$'
ANN_LOG = r'$f(log(x))$'
ANN_SIN = r'$f(sin(x))$'
ANN_COS = r'$f(cos(x))$'
ANN_TAN = r'$f(tan(x))$'

line_style = dict(linewidth=SECONDARY_LINE_WIDTH, color=MAIN_COLOR)
spines_style = dict(color=MAIN_COLOR, linewidth=0.5)
spine_arrow_style = dict(markerfacecolor=MAIN_COLOR, markeredgecolor=MAIN_COLOR, markersize=6)
ax_patch_style = dict(color='xkcd:light grey', alpha=1)
ticks_style = dict(color=MAIN_COLOR, labelcolor=MAIN_COLOR)
title_style = dict(fontsize='large', fontweight='medium', fontstyle='italic', color=TITLE_COLOR)
annotation_style = dict(color=ANNOTATION_COLOR)

# plt.rcParams['text.usetex'] = True

def lin(x):
    return x


def create_y_array(func, *args):
    return func(*args)


class Style:

    def __init__(self, ax, title='', annotation='', column=FUNCTION_COLUMN):
        self.ax = ax
        self.column = column
        self.title = title
        self.annotation = annotation

    def setup_ticks(self, y_array):
        min_tick, max_tick = np.amin(y_array), np.amax(y_array)
        self.ax.set_yticks([min_tick, max_tick])
        self.ax.tick_params(**ticks_style)
        if self.column == FUNCTION_COLUMN:
            self.ax.tick_params(axis='y', labelcolor=FUNCTION_Y_TICKS_COLOR)
        # elif self.column == DERIVATIVE_COLUMN:
        #     self.ax.tick_params(axis='x', labelcolor=DERIVATIVE_X_TICKS_COLOR)
        return max_tick

    def setup_spines(self, *invisible):
        self.ax.spines[:].set_linewidth(spines_style['linewidth'])
        self.ax.spines[:].set_color(spines_style['color'])
        self.ax.spines[list(invisible)].set_visible(False)

    def setup_patch(self):
        self.ax.patch.set_facecolor(ax_patch_style['color'])
        self.ax.patch.set_alpha(ax_patch_style['alpha'])
        if self.column == DERIVATIVE_COLUMN:
            self.ax.patch.set_alpha(SECONDARY_ALPHA)

    def setup_arrows(self):
        self.ax.spines[:].set_position(("data", 0))
        self.ax.plot(1, 0, transform=self.ax.get_yaxis_transform(), clip_on=False, marker=5, **spine_arrow_style)
        self.ax.plot(0, 1, transform=self.ax.get_xaxis_transform(), clip_on=False, marker=6, **spine_arrow_style)

    def setup_title(self):
        self.ax.set_title(self.title, **title_style)

    def setup_lines(self):
        line = self.ax.get_lines()[0]
        line.set(**line_style)
        if self.column == DERIVATIVE_COLUMN:
            line.set(color=SECONDARY_COLOR, linewidth=SECONDARY_LINE_WIDTH)

    def setup_annotation(self, y):
        if self.column == FUNCTION_COLUMN:
            self.ax.text(1, y, self.annotation,
                         horizontalalignment='left',
                         verticalalignment='top',
                         **annotation_style)

    def setup_margins(self):
        self.ax.margins(y=MARGIN_Y)

    def setup(self, y_array):
        self.setup_title()
        self.setup_patch()
        self.setup_lines()
        self.setup_spines('top', 'right')
        max_y_tick = self.setup_ticks(y_array)
        self.setup_annotation(max_y_tick)
        self.setup_margins()
        self.setup_arrows()


def make_plots():
    fig = plt.figure(dpi=150)
    x_array = np.arange(3, 30, 1)

    # Lin
    panes = fig.subfigures(8, 1)
    pane = panes[0]   
    func_axes, deriv_axes = pane.subplots(2, 1)

    y_array = create_y_array(lin, x_array)
    func_axes.plot(x_array, y_array)
    Style(func_axes, title=ANN_LIN).setup(y_array)

    y_array = create_y_array(derivative, lin, x_array)
    deriv_axes.plot(x_array, y_array)
    Style(deriv_axes, column=DERIVATIVE_COLUMN).setup(y_array)

    # Quad
    pane = panes[1]
    func_axes, deriv_axes = pane.subplots(2, 1)

    y_array = create_y_array(np.power, x_array, 2)
    func_axes.plot(x_array, y_array)
    Style(func_axes, title=ANN_QUAD).setup(y_array)

    y_array = create_y_array(derivative, lambda x: np.power(x, 2), x_array)
    deriv_axes.plot(x_array, y_array,)
    Style(deriv_axes, column=DERIVATIVE_COLUMN).setup(y_array)

    # Cubic
    pane = panes[2]
    func_axes, deriv_axes = pane.subplots(2, 1)

    y_array = create_y_array(np.power, x_array, 3)
    func_axes.plot(x_array, y_array,)
    Style(func_axes, title=ANN_CUB).setup(y_array)

    y_array = create_y_array(derivative, lambda x: np.power(x, 3), x_array)
    deriv_axes.plot(x_array, y_array)
    Style(deriv_axes, column=DERIVATIVE_COLUMN).setup(y_array)

    # Exp
    pane = panes[3]
    func_axes, deriv_axes = pane.subplots(2, 1)

    y_array = create_y_array(np.exp, x_array)
    func_axes.plot(x_array, y_array)
    Style(func_axes, title=ANN_EXP).setup(y_array)

    y_array = create_y_array(derivative, np.exp, x_array)
    deriv_axes.plot(x_array, y_array)
    Style(deriv_axes, column=DERIVATIVE_COLUMN).setup(y_array)

    # Ln
    pane = panes[4]
    func_axes, deriv_axes = pane.subplots(2, 1)

    y_array = create_y_array(np.log, x_array)
    func_axes.plot(x_array, y_array)
    Style(func_axes, title=ANN_LOG).setup(y_array)

    y_array = create_y_array(derivative, np.log, x_array)
    deriv_axes.plot(x_array, y_array)
    Style(deriv_axes, column=DERIVATIVE_COLUMN).setup(y_array)

    # Sin
    pane = panes[5]
    func_axes, deriv_axes = pane.subplots(2, 1)

    y_array = create_y_array(np.sin, x_array)
    func_axes.plot(x_array, y_array)
    Style(func_axes, title=ANN_SIN).setup(y_array)

    y_array = create_y_array(derivative, np.sin, x_array)
    deriv_axes.plot(x_array, y_array)
    Style(deriv_axes, column=DERIVATIVE_COLUMN).setup(y_array)

    # Cos
    pane = panes[6]
    func_axes, deriv_axes = pane.subplots(2, 1)

    y_array = create_y_array(np.cos, x_array)
    func_axes.plot(x_array, y_array)
    Style(func_axes, title=ANN_COS).setup(y_array)

    y_array = create_y_array(derivative, np.cos, x_array)
    deriv_axes.plot(x_array, y_array)
    Style(deriv_axes, column=DERIVATIVE_COLUMN).setup(y_array)

    # Tan
    pane = panes[7]
    func_axes, deriv_axes = pane.subplots(2, 1)

    y_array = create_y_array(np.tan, x_array)
    func_axes.plot(x_array, y_array)
    Style(func_axes, title=ANN_TAN).setup(y_array)

    y_array = create_y_array(derivative, np.tan, x_array)
    deriv_axes.plot(x_array, y_array)
    Style(deriv_axes, column=DERIVATIVE_COLUMN).setup(y_array)

    # plt.tight_layout()
    plt.show()


make_plots()
