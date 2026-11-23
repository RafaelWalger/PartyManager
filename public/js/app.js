// =====================================================================
// PartyManager — scripts usados em todas as páginas
// =====================================================================
(function () {
  "use strict";

  var raiz = document.documentElement;
  var CHAVE = "partymanager-aparencia";

  // Organizador logado: a aparência fica salva no banco (data-servidor="1").
  // Visitante e equipe: fica salva no próprio navegador.
  var salvaNoServidor = raiz.dataset.servidor === "1";

  function csrf() {
    var meta = document.querySelector('meta[name="_csrf"]');
    return meta ? meta.content : "";
  }

  function salvar() {
    var tema = raiz.dataset.tema;
    var modo = raiz.dataset.modo;
    if (salvaNoServidor) {
      var dados = new URLSearchParams({ tema: tema, modo: modo, _csrf: csrf() });
      fetch("/organizador/conta/aparencia/rapida", { method: "POST", body: dados }).catch(function () {});
    } else {
      try {
        localStorage.setItem(CHAVE, JSON.stringify({ tema: tema, modo: modo }));
      } catch (e) { /* navegador sem armazenamento: só não lembra a escolha */ }
    }
  }

  // ---------- Botão claro / escuro
  document.querySelectorAll("[data-alternar-modo]").forEach(function (botao) {
    botao.addEventListener("click", function () {
      raiz.dataset.modo = raiz.dataset.modo === "claro" ? "escuro" : "claro";
      botao.setAttribute("aria-pressed", raiz.dataset.modo === "claro");
      salvar();
    });
  });

  // ---------- Escolha de tema (prévia ao vivo)
  document.querySelectorAll("[data-escolher-tema]").forEach(function (opcao) {
    if (opcao.value === raiz.dataset.tema) opcao.checked = true;
    opcao.addEventListener("change", function () {
      raiz.dataset.tema = opcao.value;
      // No menu rápido salva na hora; na página "Conta" só mostra a prévia até clicar em Salvar
      if (opcao.form && opcao.form.hasAttribute("data-salvar-ao-escolher")) salvar();
    });
  });
  document.querySelectorAll("[data-escolher-modo]").forEach(function (opcao) {
    if (opcao.value === raiz.dataset.modo) opcao.checked = true;
    opcao.addEventListener("change", function () { raiz.dataset.modo = opcao.value; });
  });

  // ---------- Mostrar / esconder senha
  document.querySelectorAll("[data-ver-senha]").forEach(function (botao) {
    botao.addEventListener("click", function () {
      var campo = botao.parentElement.querySelector("input");
      var mostrar = campo.type === "password";
      campo.type = mostrar ? "text" : "password";
      botao.setAttribute("aria-label", mostrar ? "Esconder senha" : "Mostrar senha");
    });
  });

  // ---------- Confirmação antes de ações que não dá para desfazer
  document.querySelectorAll("form[data-confirmar]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.dataset.confirmar)) e.preventDefault();
    });
  });

  // ---------- Evita clique duplo em botões de envio (cobrança em dobro, por exemplo)
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (e.defaultPrevented) return;
      var botao = form.querySelector('button[type="submit"]:not([data-sem-trava])');
      if (botao) setTimeout(function () { botao.disabled = true; }, 0);
    });
  });

  // Ao voltar com o botão "voltar" do navegador, libera os botões de novo
  window.addEventListener("pageshow", function (e) {
    if (!e.persisted) return;
    document.querySelectorAll('button[type="submit"]').forEach(function (b) { b.disabled = false; });
  });

  // ---------- Atualiza páginas "ao vivo" (painel) sem atrapalhar quem está digitando
  var atualizar = document.querySelector("[data-atualizar-a-cada]");
  if (atualizar) {
    var segundos = parseInt(atualizar.dataset.atualizarACada, 10) || 30;
    setInterval(function () {
      var digitando = document.activeElement && /INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName);
      if (document.visibilityState === "visible" && !digitando) window.location.reload();
    }, segundos * 1000);
  }

  // ---------- Formata CPF enquanto digita
  document.querySelectorAll("[data-mascara-cpf]").forEach(function (campo) {
    campo.addEventListener("input", function () {
      var n = campo.value.replace(/\D/g, "").slice(0, 11);
      campo.value = n.replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d{1,2})$/, "$1-$2");
    });
  });

  // ---------- Botões de valor rápido (caixa de recarga)
  document.querySelectorAll("[data-valor-rapido]").forEach(function (botao) {
    botao.addEventListener("click", function () {
      var campo = document.getElementById(botao.dataset.alvo);
      campo.value = botao.dataset.valorRapido;
      campo.focus();
    });
  });
})();
