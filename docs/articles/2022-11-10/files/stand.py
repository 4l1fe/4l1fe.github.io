from functools import partial
from datetime import datetime

import numpy as np
import tornado.ioloop
import bokeh.events
from bokeh.models import ColumnDataSource, RangeTool
from bokeh.plotting import figure, show
from bokeh.sampledata.stocks import AAPL
from bokeh.layouts import column
from bokeh.application.handlers.function import FunctionHandler
from bokeh.application.application import Application
from bokeh.server.server import Server


def assign_callbacks(plot):

    def _print_out_callback(event_name, *args):
        if event_name in {'PanStart', 'PanEnd'}:
            event = args[0]
            print('Event: ', event_name, f'Data: x={event.x}, sx={event.sx}, y={event.y}, sy={event.sy}')
        elif event_name == 'RangesUpdate':
            event = args[0]
            print('Event: ', event_name, f'Data: x0={event.x0}, x1={event.x1}, y0={event.y0}, y1={event.y1}')
        else:
            print('Event: ', event_name, 'Data: ', args)

    event_names = list(bokeh.events.__all__)
    for excluded in ('DocumentEvent', 'Event', 'ModelEvent', 'PlotEvent', 'PointEvent'):
        event_names.remove(excluded)

    for event_name in event_names:
        event = getattr(bokeh.events, event_name)
        plot.on_event(event, partial(_print_out_callback, event_name))


def pan_end_callback(selected_range, event):
    start= datetime.utcfromtimestamp(selected_range.start/1000)
    end = datetime.utcfromtimestamp(selected_range.end/1000)
    print(f'Attrs on PanEnd: start={start}, end={end}')


def on_change_callback(attr, old, new):
    print(f'Attr: {attr}, old={old}, new={new}')


def make_models():
    dates = np.array(AAPL['date'], dtype=np.datetime64)
    source = ColumnDataSource(data=dict(date=dates, close=AAPL['adj_close']))
    # source = ColumnDataSource(data=dict(date=dates, close=np.random.randint(100,700, 3270)))

    data_plot = figure(height=300, width=800, tools="xpan", toolbar_location=None,
               x_axis_type="datetime", x_axis_location="above",
               background_fill_color="#efefef", x_range=(dates[1500], dates[2500]))

    data_plot.line('date', 'close', source=source)
    data_plot.yaxis.axis_label = 'Price'

    range_plot = figure(title=None,
                    height=130,
                    width=800,
                    y_range=data_plot.y_range,
                    # x_axis_type="datetime",
                    x_axis_type=None,
                    y_axis_type=None,
                    tools="",
                    toolbar_location=None,
                    background_fill_color="black")

    range_tool = RangeTool(x_range=data_plot.x_range)
    range_tool.overlay.fill_color = "yellow"
    range_tool.overlay.fill_alpha = 0.2

    range_plot.line('date', 'close', source=source, color='yellow')
    range_plot.ygrid.grid_line_color = None
    range_plot.add_tools(range_tool)
    range_plot.toolbar.active_multi = range_tool

    return data_plot, range_plot, range_tool


def make_layout():
    data_plot, range_plot, range_tool = make_models()

    # assign_callbacks(range_plot)
    range_plot.on_event(bokeh.events.PanEnd, partial(pan_end_callback, range_tool.x_range))
    # print('Initital values.', 'start=', range_tool.x_range.start, 'end=', range_tool.x_range.end)
    # range_tool.x_range.on_change('start', on_change_callback)
    # range_tool.x_range.on_change('end', on_change_callback)
    layout = column(data_plot, range_plot)
    return layout


def make_doc(doc):
    l = make_layout()
    doc.add_root(l)
    return doc


app = Application(FunctionHandler(make_doc))
srv = Server({'/': app}, io_loop=tornado.ioloop.IOLoop.current())
srv.run_until_shutdown()