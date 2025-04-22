window.onload = () => {
  let tg;

  if (window.Telegram && window.Telegram.WebApp) {
    tg = window.Telegram.WebApp;
    tg.ready();
  } else {
    console.warn("Не в Telegram WebApp — включён тестовый режим.");
    tg = {
      sendData: (d) => alert("Эмуляция sendData: " + d),
      close: () => alert("Эмуляция закрытия WebApp")
    };
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
          // можно не выводить ошибки, чтобы не мешало
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