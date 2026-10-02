// Aplicar el tema antes de pintar, compatible con script-src 'self'.
try {
  var tema = localStorage.getItem('literalevel.tema');
  if (tema && tema !== 'sistema') document.documentElement.setAttribute('data-tema', tema);
} catch (error) {}
