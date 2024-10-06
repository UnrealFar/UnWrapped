document.addEventListener("DOMContentLoaded", function() {
    var loggedIn = localStorage.getItem("id");
    var nav = document.querySelector("nav");

    nav.innerHTML = `
        <div id="navbar">
            <button id="homeButton" onclick="window.location.href='/'">UnWrapped</button>
            <div id="navButtons">
                <!-- <button id="playlistsButton" onclick="window.location.href='/playlists'">Playlists</button> -->
                <button id="profileButton" onclick="window.location.href='/profile'">
                    <img id="profileImage" src="" alt="Profile Image" style="width: 20px; height: 20px; border-radius: 50%; margin-right: 5px;">
                    Profile
                </button>
                <button id="loginButton">Log In</button>
                <button id="logoutButton">Log Out</button>
            </div>
        </div>
    `;

    if (loggedIn != null && loggedIn != "null") {
        var loginButton = document.getElementById("loginButton");
        loginButton.style.display = "none";
        var logoutButton = document.getElementById("logoutButton");
        logoutButton.style.display = "block";
        var profileButton = document.getElementById("profileButton");
        profileButton.style.display = "block";
        var profileImage = document.getElementById("profileImage");
        profileImage.src = localStorage.getItem("image");
    } else {
        var loginButton = document.getElementById("loginButton");
        loginButton.style.display = "block";
        var logoutButton = document.getElementById("logoutButton");
        logoutButton.style.display = "none";
        var profileButton = document.getElementById("profileButton");
        profileButton.style.display = "none";
    }



    document.getElementById("loginButton").addEventListener("click", function() {
        window.location.href = "/login";
    });

    document.getElementById("logoutButton").addEventListener("click", function() {
        localStorage.clear();
        window.location.href = "/logout";
    });

    var footer = document.createElement("footer");
    footer.id = "footer";
    footer.innerHTML = "Made by Farhan";
    document.body.appendChild(footer);

});