import plotly.graph_objects as go

from convertation import sqlite_output, duck_output, convert


def build():
    """Making a lines plot with time measurement data"""
    sqlite_data = convert(sqlite_output)
    duckdb_data = convert(duck_output)

    fig = go.Figure()
    x_coord_names = [f'{i}M' for i in range(1, len(sqlite_data)+1)]
    fig.add_trace(go.Scatter(x=x_coord_names, y=duckdb_data, mode='lines+markers', name='DuckDB'))
    fig.add_trace(go.Scatter(x=x_coord_names, y=sqlite_data, mode='lines+markers', name='Sqlite'))
    fig.update_layout(
        title=dict(
            text='Query execution performance. Lower is better.',
            x=0.5),
        xaxis_title='Records count',
        yaxis_title="Execution time, sec.",
        font=dict(
            size=14,
            color='black',
            family='Ubuntu mono'
        ),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    fig.show()


if __name__ == '__main__':
    build()