// =====================================================================
// Ponto de venda: carrinho na tela. O preço mostrado aqui é só para o
// funcionário acompanhar; quem calcula o valor cobrado é o servidor,
// com os preços do banco.
// =====================================================================
(function () {
  "use strict";

  var grade = document.getElementById("produtos");
  if (!grade) return;

  var lista = document.getElementById("carrinho-lista");
  var totalTela = document.getElementById("total");
  var contador = document.getElementById("contador");
  var botaoCobrar = document.getElementById("btn-cobrar");
  var campos = document.getElementById("campos-carrinho");
  var formato = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

  var carrinho = {}; // { idProduto: quantidade }

  function produto(id) {
    return grade.querySelector('[data-id="' + id + '"]');
  }

  function desenhar() {
    var total = 0;
    var itens = 0;
    lista.innerHTML = "";
    campos.innerHTML = "";

    Object.keys(carrinho).forEach(function (id) {
      var qtd = carrinho[id];
      var botao = produto(id);
      var preco = parseInt(botao.dataset.preco, 10);
      total += preco * qtd;
      itens += qtd;

      var li = document.createElement("li");
      li.innerHTML =
        '<span class="nome"></span><span class="sub">' + formato.format(preco * qtd / 100) + "</span>" +
        '<span class="unit">' + formato.format(preco / 100) + " cada</span>" +
        '<div class="mais-menos"><button type="button" aria-label="Diminuir">−</button><span>' + qtd +
        '</span><button type="button" aria-label="Aumentar">+</button></div>';
      li.querySelector(".nome").textContent = botao.dataset.nome;
      var b = li.querySelectorAll("button");
      b[0].addEventListener("click", function () { mudar(id, -1); });
      b[1].addEventListener("click", function () { mudar(id, 1); });
      lista.appendChild(li);

      var campo = document.createElement("input");
      campo.type = "hidden";
      campo.name = "q_" + id;
      campo.value = qtd;
      campos.appendChild(campo);
    });

    if (!itens) {
      lista.innerHTML = '<li class="carrinho-vazio">Toque nos produtos para montar o pedido.</li>';
    }

    grade.querySelectorAll(".produto").forEach(function (botao) {
      var qtd = carrinho[botao.dataset.id] || 0;
      botao.classList.toggle("no-carrinho", qtd > 0);
      var selo = botao.querySelector(".qtd");
      selo.textContent = qtd;
      selo.hidden = qtd === 0;
    });

    totalTela.textContent = formato.format(total / 100);
    contador.textContent = itens === 1 ? "1 item" : itens + " itens";
    botaoCobrar.disabled = itens === 0;
  }

  function mudar(id, delta) {
    var estoque = parseInt(produto(id).dataset.estoque, 10);
    var nova = Math.min(estoque, (carrinho[id] || 0) + delta);
    if (nova <= 0) delete carrinho[id]; else carrinho[id] = nova;
    desenhar();
  }

  grade.querySelectorAll(".produto").forEach(function (botao) {
    botao.addEventListener("click", function () { mudar(botao.dataset.id, 1); });
  });

  document.getElementById("btn-limpar").addEventListener("click", function () {
    carrinho = {};
    desenhar();
  });

  // Filtro por categoria
  document.querySelectorAll(".filtro").forEach(function (filtro) {
    filtro.addEventListener("click", function () {
      document.querySelectorAll(".filtro").forEach(function (f) {
        f.classList.remove("ativo");
        f.setAttribute("aria-pressed", "false");
      });
      filtro.classList.add("ativo");
      filtro.setAttribute("aria-pressed", "true");
      var categoria = filtro.dataset.categoria;
      grade.querySelectorAll(".produto").forEach(function (p) {
        p.hidden = categoria !== "todos" && p.dataset.categoria !== categoria;
      });
    });
  });

  desenhar();
})();
