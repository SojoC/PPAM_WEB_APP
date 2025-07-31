from .models import db, Contact, Congregacion, Territorio
from sqlalchemy import or_, select
from fuzzywuzzy import fuzz

class MotorBusquedaModerno:
    def __init__(self):
        # El constructor ahora está vacío. No es necesario el aprendizaje previo.
        pass

    def buscar_contactos(self, termino, limite=100):
        termino = termino.lower().strip()
        if not termino:
            # Si no hay término, devuelve los primeros contactos
            stmt = select(Contact).limit(limite)
            contactos_db = db.session.execute(stmt).scalars().all()
            return [self._formatear_contacto(c) for c in contactos_db]

        # 1. TOKENIZACIÓN: Dividimos la búsqueda del usuario en palabras clave
        terminos_usuario = set(termino.split())
        
        # 2. FILTRADO EN BASE DE DATOS: Obtenemos una lista de candidatos
        # Buscamos cualquier contacto que contenga AL MENOS UNA de las palabras
        filtros = []
        for t in terminos_usuario:
            termino_like = f"%{t}%"
            filtros.append(Contact.Nombre.ilike(termino_like))
            filtros.append(Congregacion.NombreCongregacion.ilike(termino_like))
            filtros.append(Territorio.NombreTerritorio.ilike(termino_like))

        query = select(Contact).join(Congregacion).join(Territorio).filter(or_(*filtros)).distinct()
        candidatos = db.session.execute(query.limit(200)).scalars().all() # Traemos hasta 200 candidatos

        # 3. PUNTUACIÓN EN PYTHON: Calculamos la relevancia de cada candidato
        resultados_con_score = []
        for contacto in candidatos:
            # Creamos un texto completo para cada contacto para facilitar la comparación
            texto_completo_contacto = (
                f"{contacto.Nombre.lower()} "
                f"{contacto.congregacion.NombreCongregacion.lower()} "
                f"{contacto.congregacion.Circuito.lower()}"
            ).strip()

            score_total = 0
            tokens_encontrados = 0
            
            # Comparamos cada palabra de la búsqueda del usuario con el texto del contacto
            for token_busqueda in terminos_usuario:
                # Usamos token_set_ratio que es bueno para encontrar palabras desordenadas
                ratio = fuzz.token_set_ratio(token_busqueda, texto_completo_contacto)
                if ratio > 80: # Si la similitud es alta
                    score_total += ratio
                    tokens_encontrados += 1
            
            # Solo consideramos el resultado si al menos un token coincidió
            if tokens_encontrados > 0:
                # FÓRMULA CLAVE: La puntuación final se potencia por el número de tokens encontrados.
                # Si el contacto coincide con TODAS las palabras, su puntuación se dispara.
                if tokens_encontrados == len(terminos_usuario):
                    score_final = score_total * tokens_encontrados * 2 # Bonus extra por coincidencia completa
                else:
                    score_final = score_total * tokens_encontrados

                resultados_con_score.append({
                    "contacto": contacto,
                    "score": score_final
                })
        
        # 4. ORDENAR Y FORMATEAR: Ordenamos por la puntuación más alta
        resultados_con_score.sort(key=lambda x: x['score'], reverse=True)

        # Devolvemos solo los mejores resultados, formateados
        return [self._formatear_contacto(res['contacto']) for res in resultados_con_score[:limite]]

    def _formatear_contacto(self, contacto):
        """Convierte un objeto Contact de SQLAlchemy a un diccionario."""
        if not contacto or not contacto.congregacion:
            return {}
            
        return {
            "id": contacto.ContactoID,
            "nombre": contacto.Nombre,
            "telefono": contacto.Telefono,
            "circuito": contacto.congregacion.Circuito,
            "congregacion": contacto.congregacion.NombreCongregacion
        }