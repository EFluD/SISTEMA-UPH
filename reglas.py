"""
reglas.py  -  Reglas de negocio puras (sin base de datos, fáciles de probar)
"""

NOTA_APROBACION = 70  # promedio mínimo para aprobar un curso


def calcular_situacion(parcial1, parcial2, parcial3):
    """Devuelve (promedio, situación).

    - Si falta algún parcial, el curso sigue 'En proceso' y no hay promedio final.
    - Con los tres parciales: 'Aprobado' si promedio >= NOTA_APROBACION, si no 'Reprobado'.
    """
    notas = [parcial1, parcial2, parcial3]
    if any(nota is None for nota in notas):
        return None, "En proceso"
    promedio = round(sum(notas) / 3, 1)
    return promedio, "Aprobado" if promedio >= NOTA_APROBACION else "Reprobado"
