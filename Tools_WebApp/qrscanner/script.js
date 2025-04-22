window.onload = () => {
  let tg;

  if (window.Telegram && window.Telegram.WebApp) {
    tg = window.Telegram.WebApp;
    tg.ready();
  }

  if (!tg) {
    document.getElementById("status").innerText = "Ошибка: Telegram WebApp не инициализировался.";
    return;
  }

  if (typeof Html5Qrcode === "undefined") {
    document.getElementById("status").innerText = "QR-библиотека не загрузилась.";
    console.error("Html5Qrcode не определён");
    return;
  }

  const html5QrCode = new Html5Qrcode("reader");

  Html5Qrcode.getCameras().then(devices => {
    if (devices && devices.length) {
      html5QrCode.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 250 },
        (decodedText) => {
          document.getElementById("status").innerText = `Сканировано: ${decodedText}`;
          tg.sendData(decodedText);
          tg.close();
        },
        (errorMessage) => {
          console.warn(`Ошибка сканирования: ${errorMessage}`);
        }
      );
    } else {
      document.getElementById("status").innerText = "Камера не найдена.";
    }
  }).catch(err => {
    console.error("Ошибка при доступе к камере:", err);
    document.getElementById("status").innerText = "Ошибка доступа к камере.";
  });
};