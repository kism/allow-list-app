function countdown() {
  let count = 3;
  const countdownElement = document.getElementById("REDIRECT_TEXT");

  const interval = setInterval(() => {
    countdownElement.innerHTML = "Redirecting in: " + count;
    count--;

    if (count < 0) {
      window.location.href = document.getElementById("REDIRECT").innerHTML;
    }
  }, 1000);
}

if (
  document.getElementById("TITLE").innerHTML ==
  "Authentication Success!"
) {
  countdown();
}
