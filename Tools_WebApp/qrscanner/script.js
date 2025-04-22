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
function onScanSuccess(decodedText, decodedResult) {
  document.getElementById("status").innerText = `Сканировано: ${decodedText}`;
  
  tg.sendData(decodedText);   // отправка ID в бота
  tg.close();                 // авто-закрытие WebApp
}

function onScanFailure(error) {
  // Можно не выводить ошибки в UI, просто тихо
}

const html5QrCode = new Html5Qrcode("reader");
Html5Qrcode.getCameras().then(devices => {
  if (devices && devices.length) {
    html5QrCode.start(
      { facingMode: "environment" },
      {
        fps: 10,
        qrbox: 250
      },
      onScanSuccess,
      onScanFailure
    );
  }
}).catch(err => {
  document.getElementById("status").innerText = "Камера не найдена";
});