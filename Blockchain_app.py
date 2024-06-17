"""
Aplicacion de Blockchain desarrollada por Sergio Jiménez Romero y David Tarrasa Puebla
"""

import BlockChain
from uuid import uuid4
import json
from flask import Flask, jsonify, request
from argparse import ArgumentParser
import requests
import time
from threading import Thread
import platform
from multiprocessing import Semaphore

# Instancia del nodo
app = Flask(__name__)
# Instanciacion de la aplicacion
blockchain = BlockChain.Blockchain()
blockchain_backup = blockchain
mutex = Semaphore(1)
# Para saber mi ip
mi_ip = "192.168.0.27"  # direccion del nodo en windows
nodos_red = set()


def copia_seguridad():
    """
    Funcion ejecutada por un hilo que crea una copia de seguridad del blockchain cada
    60 segundos y la guarda en un json. Tiene un semáforo de exclusión mutua para evitar
    que el blockchain se modifique durante la copia de seguridad
    """
    global blockchain_backup
    while True:
        time.sleep(60)
        mutex.acquire()
        t = time.localtime()
        blockchain_backup = {
            # Solamente permitimos la cadena de aquellos bloques finales que tienen hash
            "chain": [b.toDict() for b in blockchain.bloques if b.hash is not None],
            "longitud": len(blockchain.bloques),
            "date": time.strftime("%d/%m/%Y %H:%M:%S", t),
        }
        with open(f"respaldo-nodo{mi_ip}-{puerto}.json", "w") as file:
            json.dump(blockchain_backup, file)
        mutex.release()
        print("copia seguridad", blockchain_backup)


@app.route("/transacciones/nueva", methods=["POST"])
def nueva_transaccion():
    """
    Esta funcion nos permite añdir una nueva transaccion, que pasará a la lista de transacciones
    sin confirmar del blockchain

    Returns:
        json, int: mensaje y código de respuesta
    """
    values = request.get_json()
    # Comprobamos que todos los datos de la transaccion estan
    required = ["origen", "destino", "cantidad"]
    if not all(k in values for k in required):
        return "Faltan valores", 400
    # Creamos una nueva transaccion
    mutex.acquire()
    indice = blockchain.nueva_transaccion(
        values["origen"], values["destino"], values["cantidad"]
    )
    response = {
        "mensaje": f"La transaccion se incluira en el bloque con indice {indice}"
    }
    mutex.release()
    return jsonify(response), 201


@app.route("/chain", methods=["GET"])
def blockchain_completa():
    """
    Permite mostrar la blockchain entera y su longitud

    Returns:
        json, int: la respuesta y el código de respuesta
    """
    mutex.acquire()
    response = {
        # Solamente permitimos la cadena de aquellos bloques finales que tienen hash
        "chain": [b.toDict() for b in blockchain.bloques if b.hash is not None],
        "longitud": len(blockchain.bloques),
    }
    mutex.release()
    return jsonify(response), 200


@app.route("/system", methods=["GET"])
def get_system_info():
    """
    Muestra la información del sistema en el que se está ejecutando

    Returns:
        json, int: mensaje y código de respuesta
    """
    response = {
        "maquina": platform.machine(),
        "nombre_sistema": platform.system(),
        "version": platform.version(),
    }
    return jsonify(response), 200


@app.route("/minar", methods=["GET"])
def minar():
    """
    Permite minar un bloque (es decir, conseguir un valor de prueba de trabajo tal que el
    hash empieza por tantos ceros como la dificultad). Además, añade al bloque una transacción
    de 0 al usuario con un pago por minar el bloque e integra el bloque en la blockchain.
    Antes de realizar todas estas tareas, comprueba que el blockchain de este nodo sea el más
    largo y, si no lo es, lo actualiza al más largo (y no mina el bloque, se deberán reintroducir
    las transacciones)

    Returns:
        json, int: el mensaje y el código de respuesta
    """
    mutex.acquire()
    blockchain_check = resuelve_conflictos(nodos_red)
    if blockchain_check == 400:
        response = {"mensaje": "El blockchain de la red está corrupto"}
        mutex.release()
        return jsonify(response), 400
    elif blockchain_check:
        response = {
            "mensaje": "Ha habido un conflicto. Esta cadena se ha actualizado con una version mas larga"
        }
    elif len(blockchain.transacciones_sin_confirmar) == 0:
        response = {
            "mensaje": "No es posible crear un nuevo bloque. No hay transacciones"
        }
    else:
        indice = blockchain.nueva_transaccion(0, mi_ip, 1)
        hash_previo = blockchain.bloques[-1].hash
        nuevo_bloque = blockchain.nuevo_bloque(hash_previo)
        hash_bloque = blockchain.prueba_trabajo(nuevo_bloque)
        blockchain.integra_bloque(nuevo_bloque, hash_bloque)
        print(nuevo_bloque.transacciones)
        response = {
            "hash_bloque": hash_bloque,
            "hash previo": hash_previo,
            "indice": indice,
            "mensaje": "Nuevo bloque minado",
            "prueba": nuevo_bloque.prueba,
            "transacciones": nuevo_bloque.transacciones,
        }
    mutex.release()
    return jsonify(response), 200


@app.route("/nodos/registrar", methods=["POST"])
def registrar_nodos_completo():
    """
    Esta funcion la realiza un nodo que registra a los nodos y actualiza
    su blockchain a la del nodo que ejecuta esta función

    Returns:
        json, int: el mensaje y código de respuesta
    """
    values = request.get_json()
    global blockchain, nodos_red

    nodos_nuevos = values.get("direccion_nodos")
    if nodos_nuevos is None:
        return "Error: No se ha proporcionado una lista de nodos", 400
    all_correct = True
    nodos_red = set(nodos_nuevos)

    mutex.acquire()
    for nodo in nodos_nuevos:
        data = {
            "nodos_direcciones": list(nodos_red - {nodo})
            + [f"http://{mi_ip}:{puerto}"],
            "blockchain": [
                bloque.toDict()
                for bloque in blockchain.bloques
                if bloque.hash is not None
            ],
        }
        # Envías el dato al nodo nuevo
        response = requests.post(
            nodo + "/nodos/registro_simple",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )
        if response.status_code == 201:
            all_correct = True
    mutex.release()
    if all_correct:
        response = {
            "mensaje": "Se han incluido nuevos nodos en la red",
            "nodos_totales": list(nodos_red - {f"http://{mi_ip}:{puerto}"}),
        }
    else:
        response = {
            "mensaje": "Error notificando el nodo estipulado",
        }
    return jsonify(response), 201


@app.route("/nodos/registro_simple", methods=["POST"])
def registrar_nodo_actualiza_blockchain():
    """
    Con esta funcion actualizamos la blockchain de un nodo que se
    registra a la del nodo que realiza el registro

    Returns:
        str, int: el mensaje y el codigo de respuesta
    """
    # Obtenemos la variable global de blockchain
    global blockchain
    read_json = request.get_json()
    nodes_addreses = read_json.get("nodos_direcciones")
    blockchain_recibida = read_json.get("blockchain")
    blockchain_leida = None
    blockchain_temporal = BlockChain.Blockchain(blockchain_recibida[0]["timestamp"])
    for bloque_json in blockchain_recibida[1:]:
        bloque = BlockChain.Bloque(
            indice=bloque_json["indice"],
            transacciones=bloque_json["transacciones"],
            timestamp=bloque_json["timestamp"],
            hash_previo=bloque_json["hash_previo"],
            prueba=bloque_json["prueba"],
        )
        if not blockchain_temporal.integra_bloque(bloque, bloque_json["hash"]):
            return "El blockchain de la red está corrupto", 400
    blockchain_leida = blockchain_temporal
    # Actualizamos la lista de nodos
    nodos_red.update(nodes_addreses)
    if blockchain_leida is None:
        return "El blockchain de la red esta currupto", 400
    else:
        blockchain = blockchain_leida
        return (
            "La blockchain del nodo"
            + str(mi_ip)
            + ":"
            + str(puerto)
            + "ha sido correctamente actualizada",
            200,
        )


@app.route("/ping", methods=["GET"])
def ping():
    """
    El nodo envía una petición al resto de nodos para ver que estén funcionando

    Returns:
        json, int: el mensaje y el codigo de respuesta
    """
    host_info = request.host_url  # Dirección IP y puerto del nodo que inicia el PING
    ping_message = {"origen": host_info, "mensaje": "PING", "timestamp": time.time()}
    respuestas = []
    for nodo in nodos_red:
        start_time = time.time()
        response = requests.post(nodo + "/pong", json=ping_message)
        end_time = time.time()

        if response.status_code == 200:
            retardo = end_time - start_time
            respuesta_pong = response.json()
            respuesta_pong["Retardo"] = retardo
            respuestas.append(respuesta_pong)

    respuesta_final = "#".join(
        [
            f"PING de {ping_message['origen']} Respuesta: PONG {r['origen_respuesta']} Retardo: {r['Retardo']}"
            for r in respuestas
        ]
    )

    if len(respuestas) == len(nodos_red):
        respuesta_final += "#Todos los nodos responden"
    else:
        respuesta_final += "#Algunos nodos no respondieron"

    return jsonify({"respuesta_final": respuesta_final}), 200


@app.route("/pong", methods=["POST"])
def pong():
    """
    Los nodos responden de acuerdo al protocolo IMC

    Returns:
        json, int: el mensaje y el código de respuesta
    """
    data = request.get_json()
    respuesta = {
        "origen_respuesta": request.host_url,  # Dirección IP y puerto del nodo que responde
        "mensaje_original": data["mensaje"],
        "mensaje_respuesta": "PONG",
    }
    return jsonify(respuesta), 200


def resuelve_conflictos(nodes_addresses):
    """
    Mecanismo para establecer el consenso y resolver los conflictos, comparando la
    longitud del blockchain del nodo con la del resto de nodos registrados

    Args:
        nodes_addresses (set): las ip de los nodos

    Returns:
        bool/int: Si la blockchain ha sido reemplazada o no o 400 si ha habido un error
    """
    global blockchain
    longitud_actual = len(blockchain.bloques)
    ha_cambiado = False
    blockchain_temporal = blockchain
    # [Codigo a completar]
    addresses = nodes_addresses.copy()
    own_address = f"http://{mi_ip}:{puerto}"
    if own_address in addresses:
        addresses.remove(f"http://{mi_ip}:{puerto}")
    for nodo in addresses:
        response = requests.get(str(nodo) + "/chain")
        if response.status_code == 200:
            cadena_nodo = response.json()["chain"]

            if len(cadena_nodo) > longitud_actual:
                ha_cambiado = True
                blockchain_temporal = BlockChain.Blockchain(cadena_nodo[0]["timestamp"])

                for bloque_json in cadena_nodo[1:]:
                    bloque = BlockChain.Bloque(
                        indice=bloque_json["indice"],
                        transacciones=bloque_json["transacciones"],
                        timestamp=bloque_json["timestamp"],
                        hash_previo=bloque_json["hash_previo"],
                        prueba=bloque_json["prueba"],
                    )

                    if not blockchain_temporal.integra_bloque(
                        bloque, bloque_json["hash"]
                    ):
                        return 400
    blockchain = blockchain_temporal
    return True if ha_cambiado else False


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-p", "--puerto", default=5000, type=int, help="puerto para escuchar"
    )
    args = parser.parse_args()
    puerto = args.puerto
    t = Thread(target=copia_seguridad)
    t.start()
    app.run(host="0.0.0.0", port=puerto)
    t.join()
