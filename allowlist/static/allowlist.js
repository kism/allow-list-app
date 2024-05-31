fetch("checkauth", {
  method: "GET",
}).then((response) => {
  if (response.ok) {
    document.getElementById("CONNECTION_TEST").innerHTML = `Already authenticated!`;
    document.getElementById("CONNECTION_TEST").style.color = "#CCFFCC";
  }
});
