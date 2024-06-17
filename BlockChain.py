"""
Implementación de blockchain de Sergio Jiménez Romero y David Tarrasa Puebla
"""

from typing import List
import json
import hashlib
import time


class Bloque:
    def __init__(
        self,
        indice: int,
        transacciones: List,
        timestamp: int,
        hash_previo: str,
        prueba: int = 0,
    ):
        """
        Constructor de la clase 'Bloque'

        Args:
            indice (int): ID unico del bloque
            transacciones (List): Lista de transacciones
            timestamp (int): Momento en que el bloque fue generado.
            hash_previo (str): hash previo_
            prueba (int, optional): prueba de trabajo. Por defecto es 0.
        """
        self.indice = indice
        self.transacciones = transacciones
        self.timestamp = timestamp
        self.hash_previo = hash_previo
        self.prueba = prueba
        self.hash = None

    def calcular_hash(self):
        """
        Devuelve el hash de un bloque

        Returns:
            str: el hash del bloque
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def toDict(self):
        """
        Este método devuelve los parámetros de un bloque como un diccionario

        Returns:
            dict: los distintos parámetros del bloque en un diccionario
        """
        return {
            "hash": self.hash,
            "hash_previo": self.hash_previo,
            "indice": self.indice,
            "prueba": self.prueba,
            "timestamp": self.timestamp,
            "transacciones": self.transacciones,
        }


class Blockchain(object):
    def __init__(self, time=time.time()):
        """
        Constructor de la clase 'Blockchain'. Al inicializar la clase generamos tambén el primer
        bloque. El argumento de time es opcional para poder especificar un timestamp si queremos
        reconstruir una blockchain

        Args:
            time (float, optional): Timestamp concreto por si queremos reconstruir una blockchain. Defaults to time.time().
        """
        self.dificultad = 4
        self.bloques = []
        self.transacciones_sin_confirmar = []
        self.indice = 1
        self.primer_bloque(time)

    def primer_bloque(self, time):
        bloque0 = Bloque(1, [], time, 1)
        bloque0.hash = bloque0.calcular_hash()
        self.indice += 1
        self.bloques.append(bloque0)

    def nuevo_bloque(self, hash_previo: str) -> Bloque:
        """
        Crea un nuevo bloque a partir de las transacciones que no estan confirmadas

        Args:
            hash_previo (str): el hash del bloque anterior a la cadena

        Returns:
            Bloque: el nuevo bloque
        """

        transacciones = self.transacciones_sin_confirmar.copy()
        bloque_nuevo = Bloque(self.indice, transacciones, time.time(), hash_previo)
        self.transacciones_sin_confirmar.clear()
        self.indice += 1
        return bloque_nuevo

    def nueva_transaccion(self, origen: str, destino: str, cantidad: int) -> int:
        """
        Crea una nueva transaccion a partir de un origen, un destino y una cantidad
        y la incluye en la lista de transacciones

        Args:
            origen (str): el que envía la transacción
            destino (str): el que la recibe
            cantidad (int): la cantidad

        Returns:
            int: el indice del bloque que va a almacenar la transacción
        """
        self.transacciones_sin_confirmar.append(
            {
                "origen": origen,
                "destino": destino,
                "cantidad": cantidad,
                "tiempo": time.time(),
            }
        )
        return self.indice

    def prueba_trabajo(self, bloque: Bloque) -> str:
        """
        Algoritmo simple de prueba de trabajo:
        - Calculara el hash del bloque hasta que encuentre un hash que empiece
        por tantos ceros como dificultad.
        - Cada vez que el bloque obtenga un hash que no sea adecuado,
        incrementara en uno el campo de 'prueba' del bloque

        Args:
            bloque (Bloque): objeto de tipo bloque

        Returns:
            str: el hash del nuevo bloque (dejará el campo de hash del bloque sin modificar)
        """
        hash = bloque.calcular_hash()
        while hash[: self.dificultad] != "0" * self.dificultad:
            bloque.prueba += 1
            hash = bloque.calcular_hash()
        return hash

    def prueba_valida(self, bloque: Bloque, hash_bloque: str) -> bool:
        """
        Metodo que comprueba si el hash_bloque comienza con tantos ceros como la
        dificultad estipulada en el blockchain
        Ademas comprobara que hash_bloque coincide con el valor devuelto del
        metodo de calcular hash del bloque.

        Args:
            bloque (Bloque): un objeto de tipo bloque
            hash_bloque (str): el hash del bloque

        Returns:
            bool: dice si el valor de prueba es correcto
        """
        try:
            return (
                hash_bloque == bloque.calcular_hash()
                and hash_bloque[: self.dificultad] == "0" * self.dificultad
            )
        except:
            return False

    def integra_bloque(self, bloque_nuevo: Bloque, hash_prueba: str) -> bool:
        """
        Metodo para integrar correctamente un bloque a la cadena de bloques.
        Debe comprobar que hash_prueba es valida y que el hash del bloque ultimo
        de la cadena coincida con el hash_previo del bloque que se va a integrar.
        Si pasa las comprobaciones, actualiza el hash del bloque nuevo a integrar
        con hash_prueba, lo inserta en la cadena y hace un reset de las transacciones
        no confirmadas (vuelve a dejar la lista de transacciones no confirmadas a
        una lista vacia)

        Args:
            bloque_nuevo (Bloque): el nuevo bloque que se va a integrar
            hash_prueba (str): la prueba de hash

        Returns:
            bool: True si se ha podido ejecutar bien y False en caso contrario (si
                  no ha pasado alguna prueba)
        """
        if bloque_nuevo.hash_previo == self.bloques[-1].hash and self.prueba_valida(
            bloque_nuevo, hash_prueba
        ):
            bloque_nuevo.hash = hash_prueba
            self.bloques.append(bloque_nuevo)
            return True
        else:
            return False
