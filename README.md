# CarTrust

Marketplace Flask para carros usados de concesionarios verificados en Medellin.

## Ejecutar en VS Code

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Abre `http://127.0.0.1:5000`.

## Vista previa directa

No abras archivos dentro de `templates/` directamente: son plantillas Flask/Jinja y el navegador las mostrara sin renderizar.

Para ver una preview igual a la app:

- Con servidor Flask: abre `http://127.0.0.1:5000/preview-web`.
- Como archivo directo: abre `CarTrust_vista_previa_web.html`.

Si cambias diseno o JS, regenera la vista directa con:

```bash
python scripts/build_static_preview.py
```

## Publicar en internet

La app ya incluye `Procfile`, `Dockerfile`, `requirements.txt`, `.env.example` y configuracion de VS Code.

### 1. Subir a GitHub

```bash
cd /ruta/a/cartrust
git init
git add .
git commit -m "Primera version de CarTrust"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/cartrust.git
git push -u origin main
```

No subas `.env`, `.venv`, `instance/*.sqlite3` ni archivos de `static/uploads`; ya estan excluidos por `.gitignore`.

### 2. Desplegar en Render o Railway

Opcion recomendada para esta version Flask:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --bind 0.0.0.0:$PORT app:app`
- Variables: `SECRET_KEY`, `SESSION_COOKIE_SECURE=true`, `DATABASE_PATH`.

Para una prueba publica rapida puedes usar SQLite. Para negocio real, migra a PostgreSQL y guarda imagenes en S3, Cloudinary o un bucket similar, porque los discos temporales de hosting pueden borrar archivos subidos.

### 3. Antes de cobrar en produccion

Conecta una pasarela real como Wompi, PayU o Mercado Pago, activa HTTPS, completa datos de sociedad operadora, NIT, domicilio, PQR, politica de tratamiento de datos, terminos, autorizaciones comerciales y validacion juridica final.

## Cuentas y roles

- Particular: registra cedula, compra, usa el asesor, consulta electrolineras y crea intenciones de pago.
- Concesionario: registra razon social, NIT, matricula mercantil, camara de comercio, representante legal y datos de contacto; publica carros usados. En el modo actual solo se aceptan concesionarios de Medellin.
- Aseguradora: registra razon social, NIT, representante legal y codigo/registro SFC o SUCIS; publica productos como seguro, asistencia vial o garantia extendida.

Rutas principales: `/confianza`, `/registro`, `/login`, `/cuenta`, `/publicar`, `/aseguradora/productos/nuevo` y `/pagos`.

Las cuentas empresariales quedan con estado `pending_review` hasta validacion externa. El sello "verificado" debe activarse solo despues de revisar RUT/registro mercantil o supervision SFC/SUCIS.

## Pagos

El flujo de `/pagos` crea intenciones de pago y evita capturar datos sensibles. Para produccion debe conectarse a una pasarela como Wompi, PayU o Mercado Pago con tokenizacion y credenciales reales. Estan habilitados metodos digitales como PSE, tarjetas tokenizadas, Nequi, DaviPlata, Boton Bancolombia y transferencia online. No se habilitan pagos fisicos como Efecty, corresponsales o efectivo.

## Datos integrados

- Del HTML de navegacion: hero claro, buscador protagonista, KPIs, flujo sin registro, asesor y confianza visible.
- Del Pages: compra usada en Colombia como decision financiera sensible, desconfianza estructural, red de aliados, servicios conexos, fidelizacion/referidos y seguridad/monitoreo como crecimiento futuro.
- De la evolucion CarTrust: `/confianza` incluye 1000 referencias internas de vehiculos populares en Colombia y muestra las publicaciones activas como Oferta CarTrust con concesionario aliado referido.

## Asesor inteligente

El asesor usa un flujo didactico de 7 pasos con progreso, tips de compra, perfil vivo y recomendacion 0-100. El calculo se ejecuta sobre el inventario local mediante reglas propias, por lo que no consume tokens de IA ni depende de llamadas externas. Incluye fallback local de iconos para que la vista previa no dependa del CDN de Lucide.

## Legal

El cumplimiento aparece al final de la pagina para no interrumpir la compra. Antes de produccion real deben completarse datos de la sociedad, NIT, domicilio, PQR y revision juridica.

La app incluye proteccion CSRF en formularios, cookies de sesion HttpOnly/SameSite y configuracion `SESSION_COOKIE_SECURE` para activar cookies seguras cuando se publique bajo HTTPS.
