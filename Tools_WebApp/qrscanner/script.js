window.onload = () => {
  const tg = window.Telegram?.WebApp;

  if (!tg) {
    document.getElementById("status").innerText = "Ошибка: Telegram WebApp не обнаружен.";
    console.warn("НЕ В Telegram WebApp — включён тестовый режим.");
    return;
  }

  tg.ready(); // Telegram готов

  const html5QrCode = new Html5Qrcode("reader");

  Html5Qrcode.getCameras().then(devices => {
    if (devices && devices.length) {
      html5QrCode.start(
        { facingMode: "environment" },
        { fps: 25, qrbox: 300 },
        (decodedText) => {
          document.getElementById("status").innerText = `Сканировано: ${decodedText}`;
          tg.sendData(decodedText);
          setTimeout(() => tg.close(), 500);
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