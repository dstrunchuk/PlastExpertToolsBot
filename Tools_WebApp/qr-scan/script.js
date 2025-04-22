const tg = window.Telegram.WebApp;
tg.expand();

function sendScannedId(qrText) {
  fetch("https://api.telegram.org/bot" + tg.initDataUnsafe.bot.token + "/sendMessage", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: tg.initDataUnsafe.user.id,
      text: "QR:" + qrText
    })
  }).then(() => {
    tg.close(); // Закрываем WebApp после отправки
  });
}

function onScanSuccess(decodedText, decodedResult) {
  html5QrcodeScanner.clear();
  sendScannedId(decodedText);
}

const html5QrcodeScanner = new Html5QrcodeScanner(
  "reader", { fps: 10, qrbox: 250 }, false
);
html5QrcodeScanner.render(onScanSuccess);