# Relevo Blender para central

13 septiembre 2026, Codex. Trabajo exclusivo en `.claude/worktrees/boca3d`,
partiendo de `7aef8f8`. Sin merge a master, despliegue, compras ni servicios de IA.
Se leyeron las instrucciones del repo, las skills de equipo/correccion/prueba
visual y los mensajes pertinentes del chat central. No se modificaron sus chats.

## Entregado

- `cara.py` genera `cara.glb` con siete piezas propias: labios superior e
  inferior con comisuras afinadas y borde de contacto, perfil de nariz,
  techo nasal, faringe, garganta y suelo bucal biselado. Peso: 187.496 bytes.
- El suelo y el labio inferior siguen la mandibula. El encuadre conserva
  el perfil completo de lado y de frente a 1280 y 390 px.
- La demo carga cara y lengua de Blender por defecto. `?lengua=0&cara=0`
  permite compararlas con el respaldo. Si falta el GLB o alguna pieza esperada,
  el visor mantiene las piezas simples.
- La revision visual encontro un fallo previo en /theta/: la punta de lengua
  no llegaba al hueco entre incisivos. Se corrigio el morfo interdental.
  El validador Python usaba mandibula completa sin giro mientras escena.ts
  aplica factor 0,3 mas giro; ahora ambos calculan la misma transformacion.

## Verificado

- Blender 2.93 exporta ambos GLB. La lengua comprueba 53 poses: exceso de techo
  y heuristica de pliegue maximos 0,0 con los umbrales del guion.
- Punta interdental en coordenadas mundiales, tanto Python como Three.js:
  x=-3,0148; y entre -0,1311 y -0,0067. El extremo anterior esta delante de los
  incisivos y dentro de su hueco vertical comprobado (-0,41..0,45).
- `npm.cmd test -- --watch=false`: 19/19 pruebas pasan. Las advertencias
  getContext de jsdom pertenecen al respaldo sin WebGL que esas pruebas ejercitan.
- `npm.cmd run build`: pasa. La boca experimental sigue fuera del bundle publico.
- `node tools/boca3d_demo.mjs`: pasa.
- `probar_blender.mjs`: Playwright/Chrome propio, dos viewports (1280x900,
  390x844 con tacto), 24 capturas de /p i u theta h ng/ de lado y frente.
  Sin errores JS, desbordamiento horizontal ni pixeles pegados a los bordes
  del canvas; canvas no vacio; poses distintas; /h/ cambia pixeles durante
  el ciclo y muestra aire; GLB roto conserva respaldo. Prueba tambien la
  posicion de la punta con `Mesh.getVertexPosition` y su matriz mundial.
- Revision visual de capturas por el agente y el coordinador. El agente reviso
  encuadre, sello /p/, lengua visible de lado, punta /theta/ y suelo menos
  angular; el coordinador reviso /ng/ lateral y /theta/ movil. No hubo revision
  humana de Miguel.

Capturas y metricas no versionadas: `build/boca3d_pruebas/`. Destacan
`desktop_p_frente.png`, `desktop_ng_lado.png`, `movil_theta_lado.png`.

## Demo local

Servidor nuevo, solo loopback: http://127.0.0.1:61229/ (PID 21428).
Arrancado oculto con `node tools/boca3d_demo/servir.mjs` desde este worktree.
Logs: `build/boca3d-servidor.log` y `build/boca3d-servidor.err`.
Para detenerlo en esta sesion: `Stop-Process -Id 21428`, comprobando antes
que ese PID siga correspondiendo a este servidor (un PID puede reutilizarse).
Para relanzar: `node tools/boca3d_demo/servir.mjs`; elige e imprime otro puerto libre.
No es un enlace publico ni accesible desde el movil por la red.

## Limites y siguiente paso

- Es un corte didactico mejorado, no una cara fotorrealista ni anatomia
  clinicamente validada. Dientes, encias y velo conservan geometria simple;
  nariz/faringe son perfiles extruidos suaves, no organos detallados.
- La prueba de techo es aproximada y de vertices en poses estaticas; la de
  pliegue es una heuristica. No demuestra ausencia de toda interseccion de
  triangulos durante coarticulacion ni correccion fonetica de las 53 poses.
- No se midieron FPS en un movil real ni se hizo auditoria anatomica externa.
- La app Angular publica no integra este componente/assets. Central debe
  revisar la demo, decidir integracion diferida y coordinar API/front/despliegue;
  no importar todo el worktree a master a ciegas, que parte de una base anterior.
- `build/` contiene solo salidas locales de este trabajo y queda sin versionar.

No hay procesos de prueba en segundo plano: solo queda el servidor de demo
identificado arriba, creado expresamente para que Miguel pueda abrirlo.
