const tg = window.Telegram.WebApp;
tg.ready();

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