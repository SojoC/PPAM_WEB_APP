import re
from core.models import db, User, Congregacion, Territorio
from sqlalchemy import or_, select
from fuzzywuzzy import fuzz, process

class MotorBusquedaModerno:
    def __init__(self):
        self.vocabulario = set()

    def init_app(self, app):
        with app.app_context():
            self._aprender_vocabulario()

    def _aprender_vocabulario(self):
        print("🧠 Aprendiendo vocabulario...")
        try:
            textos = (db.session.execute(select(User.nombre_completo)).scalars().all() +
                      db.session.execute(select(User.telefono)).scalars().all() +
                      db.session.execute(select(Congregacion.nombre)).scalars().all() +
                      db.session.execute(select(Congregacion.circuito)).scalars().all() +
                      db.session.execute(select(Territorio.nombre)).scalars().all())
            
            palabras_unicas = set()
            for texto in textos:
                if texto:
                    palabras = re.split(r'[\s/,-]+', texto.lower())
                    palabras_unicas.update(p for p in palabras if p)
            self.vocabulario = palabras_unicas
            print(f"✅ Conocimiento adquirido: {len(self.vocabulario)} palabras únicas.")
        except Exception as e:
            print(f"⚠️ Error al aprender vocabulario: {e}")

    def _interpretar_termino(self, termino):
        """Usa el vocabulario para corregir errores ortográficos."""
        if not self.vocabulario or len(termino) < 3 or termino.isdigit():
            return termino
        mejor_match, score = process.extractOne(termino, self.vocabulario)
        return mejor_match if score >= 75 else termino

    def buscar_contactos(self, termino_completo):
        """
        Motor de búsqueda final que implementa filtrado, puntuación y multi-búsqueda.
        """
        termino_completo = termino_completo.lower().strip()
        
        # CORRECCIÓN: Cargar todos los usuarios si la búsqueda está vacía.
        if not termino_completo:
            todos_los_usuarios = db.session.execute(select(User).limit(502)).scalars().all()
            return [self._formatear_usuario(u) for u in todos_los_usuarios]

        # Dividir la búsqueda principal por comas para multi-búsqueda
        sub_consultas = [s.strip() for s in termino_completo.split(',') if s.strip()]
        resultados_finales = {}

        for sub_termino in sub_consultas:
            # 1. INTERPRETACIÓN Y TOKENIZACIÓN
            terminos_usuario = {self._interpretar_termino(t) for t in sub_termino.split()}
            
            # 2. FILTRADO AMPLIO EN LA BASE DE DATOS (FASE 1)
            filtros = []
            for t in terminos_usuario:
                termino_like = f"%{t}%"
                filtros.append(User.nombre_completo.ilike(termino_like))
                filtros.append(User.telefono.ilike(termino_like))
                filtros.append(Congregacion.nombre.ilike(termino_like))
                filtros.append(Congregacion.circuito.ilike(termino_like))
                filtros.append(Territorio.nombre.ilike(termino_like))

            query = select(User).join(User.congregacion).outerjoin(Congregacion.territorios).filter(or_(*filtros))
            candidatos = db.session.execute(query.distinct().limit(200)).scalars().all()

            # 3. PUNTUACIÓN PRECISA EN PYTHON (FASE 2)
            resultados_con_score = []
            for usuario in candidatos:
                texto_completo = (f"{usuario.nombre_completo.lower()} {usuario.congregacion.nombre.lower()} "
                                  f"{usuario.congregacion.circuito.lower()}").strip()
                
                tokens_encontrados = 0
                score_total = 0
                
                # REGLA DE PRECISIÓN: Damos puntos por cada término encontrado
                for token in terminos_usuario:
                    if token in texto_completo:
                        tokens_encontrados += 1
                        score_total += 100 # Puntuación alta por coincidencia directa

                # Solo consideramos resultados que coincidan con TODOS los términos
                if tokens_encontrados == len(terminos_usuario):
                    # Bonus adicional por la similitud general de la frase
                    score_total += fuzz.token_set_ratio(sub_termino, texto_completo)
                    resultados_con_score.append({"usuario": usuario, "score": score_total})

            # Ordenamos los resultados de esta sub-consulta
            resultados_con_score.sort(key=lambda x: x['score'], reverse=True)
            
            # Añadimos los mejores resultados a nuestra colección final
            for res in resultados_con_score:
                if res['usuario'].id not in resultados_finales:
                    resultados_finales[res['usuario'].id] = res['usuario']

        return [self._formatear_usuario(u) for u in resultados_finales.values()]

    def _formatear_usuario(self, usuario):
        if not usuario or not usuario.congregacion: return {}
        return {
            "id": usuario.id,
            "nombre": usuario.nombre_completo,
            "telefono": usuario.telefono,
            "circuito": usuario.congregacion.circuito,
            "congregacion": usuario.congregacion.nombre
        }