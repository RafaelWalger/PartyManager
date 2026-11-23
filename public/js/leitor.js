// =====================================================================
// Leitura de QR Code (câmera) e de pulseira NFC direto no navegador.
//
// - Leitores USB/Bluetooth funcionam sempre: eles "digitam" o código no
//   campo e apertam Enter sozinhos.
// - Câmera: usa a BarcodeDetector API (Chrome no Android e no desktop).
// - NFC: usa a Web NFC API (Chrome no Android, com o site em HTTPS).
// Se o aparelho não tiver suporte, o botão simplesmente não aparece.
// =====================================================================
(function () {
  "use strict";

  // ---------- Câmera para QR Code
  document.querySelectorAll("[data-leitor-qr]").forEach(function (botao) {
    if (!("BarcodeDetector" in window) || !navigator.mediaDevices) return;
    botao.hidden = false;

    var form = botao.closest("form") || document.querySelector(botao.dataset.form);
    var campo = form.querySelector("input[name='codigo']");
    var video = document.querySelector(botao.dataset.video);
    var detector = new window.BarcodeDetector({ formats: ["qr_code"] });
    var fluxo = null;

    function parar() {
      if (fluxo) fluxo.getTracks().forEach(function (t) { t.stop(); });
      fluxo = null;
      video.hidden = true;
      botao.textContent = "Usar câmera";
    }

    function procurar() {
      if (!fluxo) return;
      detector.detect(video).then(function (codigos) {
        if (codigos.length) {
          campo.value = codigos[0].rawValue;
          parar();
          form.requestSubmit();
        } else {
          requestAnimationFrame(procurar);
        }
      }).catch(function () { requestAnimationFrame(procurar); });
    }

    botao.addEventListener("click", function () {
      if (fluxo) { parar(); return; }
      navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } }).then(function (s) {
        fluxo = s;
        video.srcObject = s;
        video.hidden = false;
        video.play();
        botao.textContent = "Fechar câmera";
        procurar();
      }).catch(function () {
        botao.textContent = "Câmera bloqueada";
      });
    });
  });

  // ---------- NFC para pulseiras
  document.querySelectorAll("[data-leitor-nfc]").forEach(function (botao) {
    if (!("NDEFReader" in window)) return;
    botao.hidden = false;

    var form = botao.closest("form") || document.querySelector(botao.dataset.form);
    var campo = form.querySelector("input[name='uid']");
    var enviar = botao.dataset.enviar === "sim";

    botao.addEventListener("click", function () {
      var leitor = new window.NDEFReader();
      botao.textContent = "Aproxime a pulseira…";
      leitor.scan().then(function () {
        leitor.onreading = function (evento) {
          campo.value = evento.serialNumber;
          botao.textContent = "Pulseira lida";
          if (enviar) form.requestSubmit();
        };
      }).catch(function () {
        botao.textContent = "NFC indisponível";
      });
    });
  });
})();
