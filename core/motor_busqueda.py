import re
from core.models import db, User, Congregacion, Territorio
from sqlalchemy import or_, select
from fuzzywuzzy import process

class MotorBusquedaModerno:
    def __init__(self):
        self.vocabulario = set()

    def init_app(self, app):
        with app.app_context():
            self._aprender_vocabulario()

    def _aprender_vocabulario(self):
        print("🧠 Aprendiendo vocabulario...")
        try:
            # Aprendizaje completo de todos los campos de texto
            textos = (db.session.execute(select(User.nombre_completo)).scalars().all() +
                      db.session.execute(select(Congregacion.nombre)).scalars().all() +
                      db.session.execute(select(Congregacion.circuito)).scalars().all() +
                      db.session.execute(select(Territorio.nombre)).scalars().all())
            
            palabras_unicas = set()
            for texto in textos:
                if texto:
                    palabras = re.split(r'[\s/,-]+', texto.lower())
                    palabras_unicas.update(p for p in palabras if p and not p.isdigit())
            self.vocabulario = palabras_unicas
            print(f"✅ Conocimiento adquirido: {len(self.vocabulario)} palabras únicas.")
        except Exception as e:
            print(f"⚠️ Error al aprender vocabulario: {e}")

    def _interpretar_termino(self, termino):
        # Corrección ortográfica para palabras sueltas
        if not self.vocabulario or len(termino) < 3:
            return termino
        mejor_match, score = process.extractOne(termino, self.vocabulario)
        return mejor_match if score >= 80 else termino

    def _ejecutar_sub_consulta(self, sub_termino):
        # 1. SEPARACIÓN INTELIGENTE
        # Separa frases con números (ej: "monagas 1") de palabras sueltas
        terminos_numericos = re.findall(r'[a-zA-Záéíóúñ]+[ -]?\d+', sub_termino)
        texto_sin_numeros = re.sub(r'[a-zA-Záéíóúñ]+[ -]?\d+', '', sub_termino).strip()
        terminos_texto = texto_sin_numeros.split()

        # Interpretar solo los términos de texto
        terminos_interpretados = {self._interpretar_termino(t) for t in terminos_texto}
        
        query = select(User).join(User.congregacion).outerjoin(Congregacion.territorios)

        # 2. FILTRO ESTRICTO PARA FRASES CON NÚMEROS
        for t in terminos_numericos:
            # Busca la frase exacta en el campo circuito
            query = query.filter(Congregacion.circuito.ilike(f"%{t}%"))

        # 3. FILTRO FLEXIBLE PARA PALABRAS SUELTAS
        for t in terminos_interpretados:
            termino_like = f"%{t}%"
            condicion = or_(
                User.nombre_completo.ilike(termino_like),
                Congregacion.nombre.ilike(termino_like),
                Territorio.nombre.ilike(termino_like)
            )
            query = query.filter(condicion)
            
        return db.session.execute(query.distinct()).scalars().all()

    def buscar_contactos(self, termino_completo):
        # Maneja multi-búsqueda con comas
        if not termino_completo.strip():
            return []
        sub_consultas = [s.strip() for s in termino_completo.split(',') if s.strip()]
        resultados_totales = {}
        for sub_termino in sub_consultas:
            resultados_parciales = self._ejecutar_sub_consulta(sub_termino)
            for usuario in resultados_parciales:
                resultados_totales[usuario.id] = usuario
        return [self._formatear_usuario(u) for u in resultados_totales.values()]

    def _formatear_usuario(self, usuario):
        if not usuario or not usuario.congregacion: return {}
        return {
            "id": usuario.id,
            "nombre": usuario.nombre_completo,
            "telefono": usuario.telefono,
            "circuito": usuario.congregacion.circuito,
            "congregacion": usuario.congregacion.nombre
        }