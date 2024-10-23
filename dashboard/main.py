import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import paho.mqtt.client as mqtt
from collections import deque
import plotly.graph_objs as go

# Configurações do MQTT
MQTT_BROKER = "broker.hivemq.com"  # Altere para o endereço do seu broker MQTT
MQTT_PORT = 1883
TOPIC_TEMPERATURA = "casa/sala/temperatura"
TOPIC_UMIDADE = "casa/sala/umidade"

# Variáveis para armazenar dados recebidos
data_temperatura = deque(maxlen=100)  # Armazena os últimos 100 valores de temperatura
data_umidade = deque(maxlen=100)  # Armazena os últimos 100 valores de umidade
timestamps = deque(maxlen=100)


# Função chamada ao receber uma mensagem do broker MQTT
def on_message(client, userdata, message):
    try:
        decoded_message = float(message.payload.decode("utf-8"))
        if message.topic == TOPIC_TEMPERATURA:
            data_temperatura.append(decoded_message)
        elif message.topic == TOPIC_UMIDADE:
            data_umidade.append(decoded_message)

        timestamps.append(len(timestamps))  # Usando índice como timestamp
    except ValueError:
        print("Erro ao decodificar a mensagem recebida")


# Configurar o cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.subscribe([(TOPIC_TEMPERATURA, 0), (TOPIC_UMIDADE, 0)])  # Inscrever-se em ambos os tópicos
mqtt_client.loop_start()  # Iniciar loop em um thread separado

# Criar o app Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard de Sensores via MQTT"),
    dcc.Graph(id="live-graph"),
    dcc.Interval(
        id="graph-update",
        interval=1000,  # Intervalo de atualização (em milissegundos)
        n_intervals=0
    )
])


# Callback para atualizar o gráfico periodicamente
@app.callback(
    Output("live-graph", "figure"),
    Input("graph-update", "n_intervals")
)
def update_graph(n):
    fig = go.Figure()

    # Plotar os dados de temperatura
    fig.add_trace(
        go.Scatter(
            x=list(timestamps),
            y=list(data_temperatura),
            mode="lines+markers",
            name="Temperatura"
        )
    )

    # Plotar os dados de umidade
    fig.add_trace(
        go.Scatter(
            x=list(timestamps),
            y=list(data_umidade),
            mode="lines+markers",
            name="Umidade"
        )
    )

    fig.update_layout(
        xaxis=dict(title="Tempo"),
        yaxis=dict(title="Valores dos Sensores", range=[0, 40]),  # Definir range de 0 a 40 no eixo Y
        title="Temperatura e Umidade Recebidos do MQTT"
    )

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
