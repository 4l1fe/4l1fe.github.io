from decimal import Decimal
import plotly.graph_objects as go
import plotly.offline as pyo
from plotly.subplots import make_subplots


PEEWEE_KV_COEF = Decimal(10)
data = [(('N1', Decimal('63')),
         ('N2', Decimal('121')),
         ('h1', Decimal('12')),
         ('h2', Decimal('111')),
         ('Dependencies', Decimal('0')),
         ('Classes count', Decimal('2')),
         ('Graph calls', Decimal('19')),
         ('CC targets count', Decimal('42')),
         ('CC max complexity', Decimal('14'))),
        (('N1', Decimal('11')),
         ('N2', Decimal('20')),
         ('h1', Decimal('6')),
         ('h2', Decimal('19')),
         ('Dependencies', Decimal('2')),
         ('Classes count', Decimal('3')),
         ('Graph calls', Decimal('20')),
         ('CC targets count', Decimal('32')),
         ('CC max complexity', Decimal('6'))),
        (('N1', Decimal('76')),
         ('N2', Decimal('142')),
         ('h1', Decimal('35')),
         ('h2', Decimal('120')),
         ('Dependencies', Decimal('7')),
         ('Classes count', Decimal('11')),
         ('Graph calls', Decimal('12')),
         ('CC targets count', Decimal('121')),
         ('CC max complexity', Decimal('6')))
        ]
fig = make_subplots(rows=2, cols=1, specs=[[{"type": "polar"}],
                                           [{"type": "polar"}]])

categories = tuple(el[0] for el in data[0]) + (data[0][0][0], )
r = tuple(el[1] for el in data[0]) + ( data[0][0][1], )
sql_sc = go.Scatterpolar(r=r, legendgroup='sql', line=dict(color="#e45756"), theta=categories, fill='toself',
                         name='Sqlitedict')
fig.add_trace(sql_sc, row=1, col=1)
sql_sc.update(showlegend=False)
fig.add_trace(sql_sc, row=2, col=1)

r = tuple(el[1] for el in data[1]) + (data[1][0][1], )
r_init = tuple(value for value in r)
kv_sc_init = go.Scatterpolar(r=r_init, legendgroup='kv', line=dict(color="#eeca3b"), theta=categories,
                             fill='toself', name='Peewee KV')
r_scaled = tuple(value * PEEWEE_KV_COEF for value in r)
kv_sc_scaled = go.Scatterpolar(r=r_scaled, legendgroup='kv', line=dict(color="#eeca3b"), theta=categories,
                               fill='toself', name='Peewee KV', showlegend=False)
fig.add_trace(kv_sc_init, row=1, col=1)
fig.add_trace(kv_sc_scaled, row=2, col=1)

r = tuple(el[1] for el in data[2]) + (data[2][0][1],)
tiny_sc = go.Scatterpolar(r=r, legendgroup='tiny', line=dict(color="#4c78a8"), theta=categories, fill='toself',
                          name='TinyDB')
fig.add_trace(tiny_sc, row=1, col=1)
tiny_sc.update(showlegend=False)
fig.add_trace(tiny_sc, row=2, col=1)

fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
        )),
    showlegend=True,
    title=dict(
        text='Summary and Summary with scaled Peewee KV',
        xanchor='center',
        yanchor='top',
        x=0.48,
        y=0.93
    ),
    font=dict(
        color='black',
        family='Ubuntu mono'
    )

)

pyo.plot(fig)