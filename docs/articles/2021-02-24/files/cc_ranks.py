import numpy as np
import matplotlib.pyplot as plt


COLOR_MAP_NAME = 'Purples'
COLOR_MAP_VMIN = 0
COLOR_MAP_VMAX = 20
ROWS_COUNT = 5
FONT_FAMILY = 'Ubuntu mono'
FONT_WEIGHT = 'bold'


def md2lists(text: str):
    # 'Type' - 3 , 'Complexity' - 5
    data = text.splitlines()[2:]
    data = [((l := line.split('|'))[3].strip(), l[5].strip()) for line in data]
    data.sort(key=lambda el: el[0])
    types = [d[0] for d in data]
    complexities = [d[1] for d in data]
    return types, complexities


class ChartData:
    def __init__(self, file: str):
        self.types = None
        self.complexities = None
        self.shape = None
        self.title = None
        self._fill_up(file)
        self._title_by_name(file)

    def _fill_up(self, file):
        with open(file) as file:
            text = file.read()
            self.types, self.complexities = md2lists(text)
        self._convert(len(self.complexities))

    def _convert(self, size):
        quont, rem = divmod(size, ROWS_COUNT)
        additional = ROWS_COUNT - rem
        if additional != 0:
            self.types = self.types + [''] * additional
            self.complexities = self.complexities + [0] * additional
            quont += 1
        self.types = np.array(self.types, dtype=np.str_)
        self.complexities = np.array(self.complexities, dtype=np.int8)
        self.types, self.complexities = map(lambda array: np.reshape(array, (ROWS_COUNT, quont)),
                                            (self.types, self.complexities))
        self.shape = self.complexities.shape

    def _title_by_name(self, file):
        if file.startswith('sqlitedict'):
            self.title = 'Sqlitedict'
        elif file.startswith('tiny'):
            self.title = 'TinyDB'
        elif file.startswith('kv'):
            self.title = 'Peewee KV'


def main():
    chart_datas = map(ChartData, ('tiny.md', 'sqlitedict.md', 'kv.md'))
    fig, axes = plt.subplots(nrows=3, ncols=1)

    for ax, chart_data in zip(axes, chart_datas):
        im = ax.imshow(chart_data.complexities, cmap=COLOR_MAP_NAME, vmin=COLOR_MAP_VMIN, vmax=COLOR_MAP_VMAX)
        ax.tick_params(bottom=False, left=False)
        ax.tick_params(labelbottom=False, labelleft=False)
        ax.spines[:].set_visible(False)
        ax.grid(which="minor", color="black", linestyle='-', linewidth=20)
        ax.tick_params(which="minor", bottom=False, left=False)
        ax.set_title(chart_data.title, ha="center", family=FONT_FAMILY, size='medium')

        for i in range(chart_data.shape[0]):
            for j in range(chart_data.shape[1]):
                text = ax.text(j, i, chart_data.types[i, j], ha="center", va="center",
                               color="purple", size='x-small', family=FONT_FAMILY)

    cb_ax = fig.add_axes([0.9, 0.05, 0.02, 0.82])
    cbar = fig.colorbar(im, cax=cb_ax)
    cbar.ax.tick_params(labelsize='x-small')
    cbar.ax.spines[:].set_visible(False)

    fig.suptitle('Cyclomatic complexity', size='large', family=FONT_FAMILY)
    fig.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()