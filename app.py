import pandas as pd
import dash
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
import json
from urllib.request import urlopen
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:wkNBwQq1VlfFyh7wiPk8@database-ds4a.chmiwxymeztj.us-east-2.rds.amazonaws.com/finalproject')
dfOcupados = pd.read_sql("SELECT * from ocupatest2", engine.connect())
dfNameDPTO = pd.read_sql("SELECT * from departamentos2", engine.connect())

dfIncomeAverage = dfOcupados[["DPTO","INGLABO"]].groupby("DPTO", as_index=False).mean()


dfIncomeAverage2 = pd.merge(dfIncomeAverage, 
                  dfNameDPTO[['Name_Dpto', 'DPTO', 'DPTO_GRAPH']],
                  left_on='DPTO',
                  right_on='DPTO',
                  how='left')

#Errores a corregir de la tabla ocupados del DANE
#1. INGLABO eliminar el espacio e blanco
#2. FEX 2011 solo puede cargar con punto como separador de decimales por restricciones de postgress
#3. P6810S1 es necesario convertirlas en texto al igual que otras 3 facilmente identificables
#P6410S1
#P6430S1
#P6480S1
#P6765S1
#P6780S1
#P6810S1
#P6830S1
#P6880S1
#P6915S1
#P6980S1
#P6980S7A1
#P7028S1
#P7140S9A1
#P7240S1
#4 Structure for extract information for postgress postgresql://username:password@host/db_name


token = 'pk.eyJ1IjoibmV3dXNlcmZvcmV2ZXIiLCJhIjoiY2o2M3d1dTZiMGZobzMzbnp2Z2NiN3lmdyJ9.cQFKe3F3ovbfxTsM9E0ZSQ'


with urlopen('https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json') as response:
    counties = json.load(response)


for loc in counties['features']:
    loc['id'] = loc['properties']['NOMBRE_DPT']
    

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/uditagarwal/pen/oNvwKNP.css'])
app.title = "Data Colombia"



app.layout = html.Div(children=[
    html.Div(
        children=[html.H2(children="Caracteristicas Demograficas Población Colombiana", className='h2-title'),],
        className='study-browser-banner row'
    ),
    html.Div(
        className='row app-body', 
        children=[

        dcc.Graph(
            id='regional-profit-plot',
            figure={
                'data': [ go.Bar(
                    name='Regional Profit',
                    x=dfIncomeAverage2["Name_Dpto"],
                    y=dfIncomeAverage2["INGLABO"]
                    )],
            }
        ),
        
        dcc.Graph(
            id='map-plot3',
            figure={ 
                'data': [go.Choroplethmapbox(
                    geojson=counties,
                    locations=dfIncomeAverage2.Name_Dpto,
                    z=dfIncomeAverage2.INGLABO,
                    colorscale='Viridis',
                    colorbar_title="Ingresos Laborales"
                )],
                'layout': go.Layout(
                        mapbox_style="carto-positron",
                        mapbox_accesstoken=token,
                        mapbox_zoom=3,
                        mapbox_center = {"lat": 4.570868, "lon": -74.2973328}
                    )
            }
        )
])])

if __name__ == '__main__':
    app.run_server(debug=True, host= '0.0.0.0')
    
#if __name__ == "__main__":
#    app.run_server(debug=True)
