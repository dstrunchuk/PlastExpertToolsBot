window.onload = () => {
  const tg = window.Telegram?.WebApp;

  if (!tg) {
    document.getElementById("status").innerText = "Ошибка: Telegram WebApp не обнаружен.";
    return;
  }

  tg.ready(); // обязательно вызывать ready()

  if (typeof Html5Qrcode === "undefined") {
    document.getElementById("status").innerText = "QR-библиотека не загрузилась.";
    return;
  }

  const html5QrCode = new Html5Qrcode("reader");

  Html5Qrcode.getCameras()
    .then((devices) => {
      if (devices && devices.length) {
        html5QrCode.start(
          { facingMode: "environment" },
          {
            fps: 30,
            qrbox: 300,
            experimentalFeatures: {
              useBarCodeDetectorIfSupported: true
            },
            formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE]
          },
          (decodedText) => {
            document.getElementById("status").innerText = `Сканировано: ${decodedText}`;
            tg.sendData(decodedText);  // Отправка в Telegram
            setTimeout(() => tg.close(), 500); // Закрытие через 0.5 сек
          },
          (errorMessage) => {
            console.warn(`Ошибка сканирования: ${errorMessage}`);
          }
        );
      } else {
        document.getElementById("status").innerText = "Камера не найдена.";
      }
    })
    .catch((err) => {
      console.error("Ошибка доступа к камере:", err);
      document.getElementById("status").innerText = "Ошибка доступа к камере.";
    });
};