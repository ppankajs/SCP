document.querySelector("form").addEventListener("submit", async function(event) {
    event.preventDefault(); // Prevent page reload

    const email = document.querySelector("input[type='email']").value;
    const password = document.querySelector("input[type='password']").value;

    const response = await fetch("http://127.0.0.1:5000/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
    });

    const data = await response.json();
    
    if (response.ok) {
        alert("Login successful!");
        localStorage.setItem("token", data.token);  // Store JWT token
        window.location.href = "/dashboard";  // Redirect after login (optional)
    } else {
        alert("Error: " + data.message);
    }
});