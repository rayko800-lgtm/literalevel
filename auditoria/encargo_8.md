# Encargo 8 — auditoría final antes de entregar

Escrito el 10 de septiembre de 2026 por la tarde, sobre el árbol `e630dde`.

## Astra / Codex: NO se pudo, y no por el tamaño del encargo

Miguel pidió expresamente usar Astra «al máximo, con tareas no largas para que
soporte los tokens». Se comprobó el cupo **antes** de escribir nada, con una
llamada mínima —«Responde solo con la palabra LISTO»— que es para lo que sirve
esa comprobación:

```
ERROR: You've hit your usage limit. … try again at Sep 15th, 2026 8:46 AM.
```

Sigue agotado desde el 9 de septiembre por la noche. **No es cuestión de acortar
la tarea: no entra ninguna, ni la de una palabra.** Vuelve el 15 a las 8:46, y
hasta entonces no hay encargo que valga.

Queda anotado porque es la segunda vez, y la lección está en la skill: el cupo
se comprueba antes de redactar el encargo, no después de que muera a mitad.

## Fable: alcance amplio

Cuando solo hay un auditor disponible, se le da el alcance **amplio** y no el
estrecho. Lo mecánico —que una cifra coincida consigo misma en ocho archivos—
se puede barrer desde aquí con un `grep`; lo que no se puede hacer solo es que
alguien con otros puntos ciegos mire el trabajo propio.

Informe a `auditoria/informe_fable_13.md`. A ciegas: no abre `auditoria/` salvo
para escribir, y no se le dice qué se acaba de corregir.

**El método principal es la mutación**, porque es lo que ha encontrado todo lo
importante en este proyecto. Con dos avisos que se ganaron a base de disgustos:

1. **Copiar el árbol de verdad** —`app/`, las pruebas, `main.py`, el CSV del
   catálogo y los embeddings— y **verificar que el control sin mutar pasa la
   suite entera** antes de mutar nada. Si falta un archivo, fallan pruebas
   ajenas en todas las copias y los mutantes parecen cubiertos sin estarlo.
2. **Atribuir el fallo a la prueba que se espera.** «La suite falla» no basta.

Ocho frentes, en orden: pruebas que no prueban; el dinero (que ningún camino
llegue a la API saltándose la puerta, y que el cupo baje si y solo si se gasta);
concurrencia y bloqueo; el contrato de que ningún manejador levanta hacia
Gradio; las cifras publicadas en todos los archivos donde viven; la prosa
entregable y su coherencia interna; la reproducibilidad del cuadernillo; y la
aplicación.

**Una salvedad que se le dijo expresamente:** lo desplegado en el Space es más
viejo que este árbol —faltan cinco módulos por subir—, así que se audita el
código local, y si prueba el Space tiene que decir que lo que ve puede no
corresponder.
