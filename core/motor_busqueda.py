import re
from core.models import db, User, Congregacion, Territorio
from sqlalchemy import or_, select
from fuzzywuzzy import process
from collections import defaultdict

def soundex(token):
    token = token.lower()
    if not token: return ""
    replacements = (('bfpv', '1'), ('cgjkqsxz', '2'), ('dt', '3'), ('l', '4'), ('mn', '5'), ('r', '6'))
    result = token[0].upper()
    last_code = ''
    for group, code in replacements:
        if token[0] in group: last_code = code; break
    for char in token[1:]:
        for group, code in replacements:
            if char in group:
                if code != last_code: result += code
                last_code = code
                break
        else: last_code = '0'
    return (result.replace('0', '') + '000')[:4]

class MotorBusquedaModerno:
    def __init__(self):
        self.vocabulario = set()
        self.indice_abreviaturas = defaultdict(set)
        self.indice_soundex = defaultdict(set)

    def init_app(self, app):
        with app.app_context():
            self._construir_indices_inteligentes()

    def _construir_indices_inteligentes(self):
        print("🧠 Construyendo índice inteligente y fonético...")
        try:
            textos = (db.session.execute(select(User.nombre_completo)).scalars().all() +
                      db.session.execute(select(User.telefono)).scalars().all() +
                      db.session.execute(select(Congregacion.nombre)).scalars().all() +
                      db.session.execute(select(Territorio.nombre)).scalars().all() +
                      db.session.execute(select(Congregacion.circuito)).scalars().all())
            
            palabras_unicas = set()
            for texto in textos:
                if texto:
                    palabras = re.split(r'[\s/,-]+', texto.lower())
                    palabras_unicas.update(p for p in palabras if p)
            self.vocabulario = palabras_unicas
            
            for palabra in self.vocabulario:
                if len(palabra) > 2: self.indice_abreviaturas[palabra[:3]].add(palabra)
                sx = soundex(palabra)
                self.indice_soundex[sx].add(palabra)
            
            print(f"✅ Conocimiento adquirido: {len(self.vocabulario)} palabras.")
        except Exception as e:
            print(f"⚠️ Error al construir el índice: {e}")

    def _interpretar_termino(self, termino):
        if termino in self.indice_abreviaturas:
            candidatos = list(self.indice_abreviaturas[termino])
            if len(candidatos) == 1: return candidatos[0]
            mejor_match, _ = process.extractOne(termino, candidatos)
            return mejor_match
        sx = soundex(termino)
        if sx in self.indice_soundex:
            candidatos = list(self.indice_soundex[sx])
            mejor_match, _ = process.extractOne(termino, candidatos)
            return mejor_match
        if not self.vocabulario or len(termino) < 3: return termino
        mejor_match, score = process.extractOne(termino, self.vocabulario)
        return mejor_match if score >= 75 else termino

    def _ejecutar_sub_consulta(self, sub_termino):
        terminos_numericos = re.findall(r'[a-zA-Záéíóúñ]+[ -]?\d+', sub_termino)
        texto_sin_numeros = re.sub(r'[a-zA-Záéíóúñ]+[ -]?\d+', '', sub_termino).strip()
        terminos_texto_suelto = texto_sin_numeros.split() if texto_sin_numeros else []

        terminos_interpretados = {self._interpretar_termino(t) for t in terminos_texto_suelto}
        
        query = select(User).join(User.congregacion).outerjoin(Congregacion.territorios)

        for t in terminos_numericos:
            query = query.filter(Congregacion.circuito.ilike(f"%{t}%"))

        for t in terminos_interpretados:
            termino_like = f"%{t}%"
            condicion = or_(
                User.nombre_completo.ilike(termino_like),
                User.telefono.ilike(termino_like),
                Congregacion.nombre.ilike(termino_like),
                Territorio.nombre.ilike(termino_like)
            )
            query = query.filter(condicion)
            
        return db.session.execute(query.distinct()).scalars().all()

    def buscar_contactos(self, termino_completo):
        termino_completo = termino_completo.lower().strip()
        
        if not termino_completo:
            todos_los_usuarios = db.session.execute(select(User).order_by(User.nombre_completo)).scalars().all()
            return [self._formatear_usuario(u) for u in todos_los_usuarios]

        sub_consultas = [s.strip() for s in termino_completo.split(',') if s.strip()]
        resultados_totales = {}
        for sub_termino in sub_consultas:
            resultados_parciales = self._ejecutar_sub_consulta(sub_termino)
            for usuario in resultados_parciales:
                resultados_totales[usuario.id] = usuario
        
        return [self._formatear_usuario(u) for u in resultados_totales.values()]

    # En src/core/motor_busqueda.py

    def _formatear_usuario(self, usuario):
        if not usuario or not usuario.congregacion: return {}
        return {
            "id": usuario.id,
            "nombre": usuario.nombre_completo,
            "telefono": usuario.telefono,
            "circuito": usuario.congregacion.circuito,
            "congregacion": usuario.congregacion.nombre,
            # --- LÍNEA AÑADIDA PARA INCLUIR PRIVILEGIOS ---
            "privilegios": [p.nombre for p in usuario.privilegios]
        }