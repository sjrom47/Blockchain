"""
Modulo de pruebas de Sergio Jiménez Romero y David Tarrasa Puebla
"""

import requests
import json

cabecera = {"Content-type": "application/json", "Accept": "text/plain"}

# Direcciones de los nodos
nodos = [
    "http://192.168.0.27:5000",
    "http://192.168.0.63:5001",
]  # Direccion del nodo 5000 en windows , Direccion del 5001 del ubuntu en virtual box (maquina virtual) tambien se puede poner del 5001 en windows


def enviar_transaccion(nodo, transaccion):
    respuesta = requests.post(
        f"{nodo}/transacciones/nueva", data=json.dumps(transaccion), headers=cabecera
    )
    print(f"Respuesta del nodo {nodo}:")
    print(respuesta.text)


def minar_bloque(nodo):
    respuesta = requests.get(f"{nodo}/minar")
    print(f"Respuesta del nodo {nodo} al minar:")
    print(respuesta.text)


def obtener_cadena_chain(nodo):
    respuesta = requests.get(f"{nodo}/chain")
    print(f"Cadena del nodo {nodo}:")
    print(respuesta.text)


def obtener_cadena(nodo):
    respuesta = requests.get(f"{nodo}/system")
    print(f"Detalles del nodo {nodo}:")
    print(respuesta.text)


def registrar_nodos_en_primero():
    nodo_primero = nodos[0]
    nodos_a_registrar = {"direccion_nodos": nodos[1:]}
    respuesta = requests.post(
        f"{nodo_primero}/nodos/registrar",
        data=json.dumps(nodos_a_registrar),
        headers=cabecera,
    )
    print("Registrar nodos en el primer nodo:")
    print(respuesta.text)


def enviar_ping():
    for nodo in nodos:
        respuesta = requests.get(f"{nodo}/ping", headers=cabecera)
        print(f"Ping al nodo {nodo}:")
        print(respuesta.text)


registrar_nodos_en_primero()
enviar_ping()

transaccion_nueva = {"origen": "nodoA", "destino": "nodoB", "cantidad": 10}
enviar_transaccion(nodos[0], transaccion_nueva)
minar_bloque(nodos[0])

enviar_transaccion(nodos[1], transaccion_nueva)
minar_bloque(nodos[1])

for nodo in nodos:
    obtener_cadena_chain(nodo)
    obtener_cadena(nodo)
