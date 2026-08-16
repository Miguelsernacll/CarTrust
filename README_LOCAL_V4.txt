CarTrust v4 - uso local

Archivo principal:
CarTrust_v4_local.html

Como usarlo:
1. Copia este archivo a cualquier computador.
2. Haz doble clic sobre CarTrust_v4_local.html.
3. El asesor inteligente funciona sin servidor Flask.

Notas:
- No abras archivos dentro de templates/. Esos son archivos internos de Flask.
- La interaccion del asesor y la recomendacion demo estan incluidas en el HTML.
- Las fotos usan URLs externas; si el equipo no tiene internet, la pagina funciona pero algunas imagenes pueden no cargar.
- Para regenerar este archivo despues de cambios:
  python scripts/build_static_preview.py
