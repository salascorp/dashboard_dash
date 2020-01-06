import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import dash_table
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:wkNBwQq1VlfFyh7wiPk8@database-ds4a.chmiwxymeztj.us-east-2.rds.amazonaws.com/strategy')
df = pd.read_sql("SELECT * from trades", engine.connect(), parse_dates=('entry_time',))

#df = pd.read_csv('aggr.csv', parse_dates=['Entry time'])

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/uditagarwal/pen/oNvwKNP.css', 'https://codepen.io/uditagarwal/pen/YzKbqyV.css'])





def filter_df(df,exchange, leverage, start_date, end_date):
    ex = (df['exchange'] == exchange)
    lev = (df['margin'] == int(leverage))
    date = ((df['entry_time'] > start_date) & (df['entry_time'] <= end_date))
    return df[(ex & lev & date)]

def calc_returns_over_month(dff):
    out = []
    dff['YearMonth'] = pd.to_datetime(dff['entry_time'].map(lambda x: x.strftime('%Y-%m')))

    for name, group in dff.groupby('YearMonth'):
        exit_balance = group.head(1)['exit_balance'].values[0]
        entry_balance = group.tail(1)['entry_balance'].values[0]
        monthly_return = (exit_balance*100 / entry_balance)-100
        out.append({
            'month': name,
            'entry': entry_balance,
            'exit': exit_balance,
            'monthly_return': monthly_return
        })
    return out

def calc_btc_returns(dff):
    btc_start_value = dff.tail(1)['btc_price'].values[0]
    btc_end_value = dff.head(1)['btc_price'].values[0]
    btc_returns = (btc_end_value * 100/ btc_start_value)-100
    return btc_returns

def calc_strat_returns(dff):
    start_value = dff.tail(1)['exit_balance'].values[0]
    end_value = dff.head(1)['entry_balance'].values[0]
    returns = (end_value * 100/ start_value)-100
    return returns


app.layout = html.Div(children=[
    html.Div(
            children=[
                html.H2(children="Bitcoin Leveraged Trading Backtest Analysis - SalasCorp", className='h2-title'),
            ],
            className='study-browser-banner row'
    ),
    html.Div(
        className="row app-body",
        children=[
            html.Div(
                className="twelve columns card",
                children=[
                    html.Div(
                        className="padding row",
                        children=[
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Exchange",),
                                    dcc.RadioItems(
                                        id="exchange-select",
                                        options=[
                                            {'label': label, 'value': label} for label in df['exchange'].unique()
                                        ],
                                        value='Bitmex',
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ]
                            ),
                            # Leverage Selector
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Leverage"),
                                    dcc.RadioItems(
                                        id="leverage-select",
                                        options=[
                                            {'label': str(label), 'value': str(label)} for label in df['margin'].unique()
                                        ],
                                        value='1',
                                        labelStyle={'display': 'inline-block'}
                                    ),
                                ]
                            ),
                            html.Div(
                                className="three columns card",
                                children=[
                                    html.H6("Select a Date Range"),
                                    dcc.DatePickerRange(
                                        id="date-range",
                                        display_format="MMM YY",
                                        start_date=df['entry_time'].min(),
                                        end_date=df['entry_time'].max()
                                    ),
                                ]
                            ),
                            html.Div(
                                id="strat-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-returns", className="indicator_value"),
                                    html.P('Strategy Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="market-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="market-returns", className="indicator_value"),
                                    html.P('Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="strat-vs-market-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-vs-market", className="indicator_value"),
                                    html.P('Strategy vs. Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                        ]
                )
        ]),
        html.Div(
            className="twelve columns card",
            children=[
                dcc.Graph(
                    id="monthly-chart",
                    figure={
                        'data': []
                    }
                )
            ]
        ),
        html.Div(
                className="padding row",
                children=[
                    html.Div(
                        className="six columns card",
                        children=[
                            dash_table.DataTable(
                                id='table',
                                columns=[
                                    {'name': 'number', 'id': 'number'},
                                    {'name': 'trade_type', 'id': 'trade_type'},
                                    {'name': 'exposure', 'id': 'exposure'},
                                    {'name': 'entry_balance', 'id': 'entry_balance'},
                                    {'name': 'exit_balance', 'id': 'exit_balance'},
                                    {'name': 'pnl_incl_fees', 'id': 'pnl_incl_fees'},
                                ],
                                style_cell={'width': '50px'},
                                style_table={
                                    'maxHeight': '450px',
                                    'overflowY': 'scroll'
                                },
                            )
                        ]
                    ),
                    dcc.Graph(
                        id="pnl-types",
                        className="six columns card",
                        figure={}
                    )
                ]
            ),
            html.Div(
                className="padding row",
                children=[
                    dcc.Graph(
                        id="daily-btc",
                        className="six columns card",
                        figure={}
                    ),
                    dcc.Graph(
                        id="balance",
                        className="six columns card",
                        figure={}
                    )
                ]
            )
        ]
    )        
])

@app.callback(
    dash.dependencies.Output('balance', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_balance(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    balance = go.Scatter(x = dff['entry_time'],y = dff['exit_balance'],name = 'balance_overtime')
    
    
    return {
        'data': [balance],
        'layout': {'title':'Balance Overtime',
                   'height':400
        
        }
    }


@app.callback(
    dash.dependencies.Output('daily-btc', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_btc(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    btc = go.Scatter(x = dff['entry_time'],y = dff['btc_price'],name = 'btc_price')
    
    
    return {
        'data': [btc],
        'layout': {'title':'Daily btc price',
                   'height':400
        
        }
    }

@app.callback(
    dash.dependencies.Output('pnl-types', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_pnl(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    dff_long = dff[dff['trade_type']=='Long']
    dff_short = dff[dff['trade_type'] == 'Short']
    short = go.Bar(x = dff_short['entry_time'],y = dff_short['pnl_incl_fees'],name='Short')
    long = go.Bar(x = dff_long['entry_time'],y = dff_long['pnl_incl_fees'],name='Long')
    
    return {
        'data': [short,long],
        'layout': {'title':'PnL',
                   'height':400
        
        }
    }


@app.callback(
    dash.dependencies.Output('table', 'data'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return dff.to_dict('records')

@app.callback(
    [
        dash.dependencies.Output('monthly-chart', 'figure'),
        dash.dependencies.Output('market-returns', 'children'),
        dash.dependencies.Output('strat-returns', 'children'),
        dash.dependencies.Output('strat-vs-market', 'children'),
    ],
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),

    )
)
def update_monthly(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    data = calc_returns_over_month(dff)
    btc_returns = calc_btc_returns(dff)
    strat_returns = calc_strat_returns(dff)
    strat_vs_market = strat_returns - btc_returns

    return {
        'data': [
            go.Candlestick(
                open=[each['entry'] for each in data],
                close=[each['exit'] for each in data],
                x=[each['month'] for each in data],
                low=[each['entry'] for each in data],
                high=[each['exit'] for each in data]
            )
        ],
        'layout': {
            'title': 'Overview of Monthly performance'
        }
    }, f'{btc_returns:0.2f}%', f'{strat_returns:0.2f}%', f'{strat_vs_market:0.2f}%'

@app.callback(
    dash.dependencies.Output('date-range', 'start_date'),
    [
        dash.dependencies.Input('exchange-select', 'value')
    ]
)
def update_date_range (value):
    df2=df[df['exchange']==value]
    start_date = df2['entry_time'].min()
    return start_date

@app.callback(
    dash.dependencies.Output('date-range', 'end_date'),
    [
        dash.dependencies.Input('exchange-select', 'value')
    ]
)
def update_date_range (value):
    df2=df[df['exchange']==value]
    end_date = df2['entry_time'].max()
    return end_date


if __name__ == '__main__':
    app.run_server(debug=True, host= '0.0.0.0')
    
#if __name__ == "__main__":
#    app.run_server(debug=True)
