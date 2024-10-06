document.addEventListener("DOMContentLoaded", function() {
    var spotifyID = localStorage.getItem("spotify_id");
    var nav = document.querySelector("nav");

    nav.innerHTML = `
        <div id="navbar">
            <button id="homeButton" onclick="window.location.href='/'">
                <img src="/static/logo/Rectangle Logo.png" alt="Logo">
            </button>
            <div id="navButtons">
                <!-- <button id="playlistsButton" onclick="window.location.href='/playlists'">Playlists</button> -->
                <div id="profileButtonContainer">
                    <button id="profileButton" style="display:none;">
                        <img id="profileImage" src="" alt="Profile Image" style="height:70;width:70;">
                    </button>
                    <div id="dropdownMenu" class="dropdown-content">
                        <a href="/profile">View Profile</a>
                        <a href="https://open.spotify.com/user/${spotifyID}" target="_blank">Open in Spotify</a>
                        <a href="#" id="logoutLink">Logout</a>
                    </div>
                </div>
                <button id="loginButton" style="display:none;">Log In</button>
            </div>
        </div>
    `;

    if (spotifyID != null && spotifyID != "null") {
        var loginButton = document.getElementById("loginButton");
        loginButton.style.display = "none";
        var profileButton = document.getElementById("profileButton");
        profileButton.style.display = "block";
        var profileImage = document.getElementById("profileImage");
        profileImage.src = localStorage.getItem("image");
    } else {
        var loginButton = document.getElementById("loginButton");
        loginButton.style.display = "block";
        var profileButton = document.getElementById("profileButton");
        profileButton.style.display = "none";
    }

    document.getElementById("loginButton").addEventListener("click", function() {
        window.location.href = "/login";
    });

    document.getElementById("logoutLink").addEventListener("click", function() {
        localStorage.clear();
        window.location.href = "/logout";
    });

    document.getElementById("profileButton").addEventListener("click", function() {
        var dropdownMenu = document.getElementById("dropdownMenu");
        dropdownMenu.classList.toggle("show");
    });

    window.onclick = function(event) {
        if (!event.target.matches('#profileButton') && !event.target.matches('#profileButton img')) {
            var dropdowns = document.getElementsByClassName("dropdown-content");
            for (var i = 0; i < dropdowns.length; i++) {
                var openDropdown = dropdowns[i];
                if (openDropdown.classList.contains('show')) {
                    openDropdown.classList.remove('show');
                }
            }
        }
    };

    var footer = document.createElement("footer");
    footer.id = "footer";
    footer.innerHTML = "Made by Farhan";
    document.body.appendChild(footer);
});