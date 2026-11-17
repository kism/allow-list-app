function printSuccess(message) {
  document.getElementById("CONNECTION_TEST").innerHTML = message;
  document.getElementById("CONNECTION_TEST").style.color = "#00FF00";
  document.getElementById("REDIRECT").style.display = "initial";
}

function printFailure(message) {
  document.getElementById("CONNECTION_TEST").innerHTML = message;
  document.getElementById("CONNECTION_TEST").style.color = "#FFCCCC";
}

function checkAuthentication() {
  fetch("check_auth/", {
    method: "GET",
  }).then((response) => {
    if (response.ok) {
      printSuccess(`Already authenticated!`);
    }
  });
}

document.getElementById("AUTH_FORM").onsubmit = async function (event) {
  event.preventDefault(); // Prevent the default form submission

  // Collect form data, sent as json to match the AuthRequest model
  const formData = Object.fromEntries(new FormData(this));

  try {
    // Send form data using Fetch API
    const response = await fetch("authenticate/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    });

    // Check if the request was successful
    if (response.ok) {
      printSuccess(`Authenticated!`);
    } else if (response.status === 429) {
      printFailure(`Too many failed attempts, try again in a minute`);
    } else {
      printFailure(`Authentication Failure`);
    }
  } catch (error) {
    // Handle errors (e.g., display an error message)
    printFailure("Form submission failed: " + error.message);
  }
};

checkAuthentication();
