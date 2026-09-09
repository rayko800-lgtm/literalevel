# Auditoría 6: corpus externo de British Council

**Recuento provisional: CRÍTICO 0 · SERIO 0 · MENOR 1.**

Informe en curso, iniciado en cuanto hubo evidencia sólida. Fecha: 9 de septiembre de 2026. Revisión inicial del repositorio: `425750f`. Alcance exclusivo: `auditoria/encargo_6.md`. No se han abierto otros informes de auditoría ni modificado otros archivos del proyecto.

## A. Integridad del corpus y manifiesto

En comprobación: inventario independiente en Downloads, contraste de nombres, contenido y fechas, y comparación exacta con el manifiesto.

## B. Aritmética de las exclusiones

Pendiente de ejecución: 59 − 2 − 10 = 47; identificación y motivo individual de las exclusiones; recuento estricto de 31. El comando `python` no está disponible en el PATH de esta sesión. El ejecutable de `D:/ll_bench/venv_cuda/Scripts/python.exe` devuelve «No Python at» para su intérprete base de Microsoft Store. Se está buscando otro intérprete instalado; esto es una limitación del entorno de auditoría, no un defecto atribuido al proyecto.

## C. Propagación de las cifras

### M1. MENOR: dos explicaciones del cuadernillo conservan la media antigua de A2

**Evidencia:** `entrega/notebook_proyecto.py:1751` y `entrega/notebook_proyecto.py:1984` comparan A1 y A2 como «0,504 frente a 0,548». El propio cuadernillo declara A2 = 0,5561 y n = 8 en `entrega/notebook_proyecto.py:1701` y `entrega/notebook_proyecto.py:1702`, y 47 textos en `entrega/notebook_proyecto.py:1704`. La búsqueda con `grep -n` verifica la contradicción sin depender de inferencia sobre el modelo.

**Consecuencia:** la actualización no llegó a las dos interpretaciones narrativas. A tres decimales, 0,5561 se escribe 0,556, no 0,548. La conclusión cualitativa sobre la cercanía de A1 y A2 no queda invalidada por esta corrección.

**Corrección propuesta, no aplicada:** sustituir 0,548 por 0,556 en ambas líneas, una vez terminada la reproducción numérica.

## Lo que comprobé y salió limpio

- La tabla del cuadernillo contiene n = [3, 8, 12, 12, 12] y medias [0,5040; 0,5561; 0,9276; 1,2414; 1,4952] (`entrega/notebook_proyecto.py:1701`, `:1702`).
- El fichero de datos de la figura contiene esas mismas cinco medias y esos tamaños (`entrega/datos_figuras/validacion.dat:2` a `:6`). Su suma es 47. Esta es todavía una comprobación de coherencia documental; la ejecución del modelo se documentará por separado.
