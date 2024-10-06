document.addEventListener("DOMContentLoaded", function() {
    const user = {
        id: localStorage.getItem("id"),
        spotify_id: localStorage.getItem("spotify_id"),
        country: localStorage.getItem("country"),
        display_name: localStorage.getItem("display_name"),
        email: localStorage.getItem("email"),
        follower_count: localStorage.getItem("follower_count"),
        image: localStorage.getItem("image"),
        product: localStorage.getItem("product")
    };

    // Populate the HTML elements with the user data
    document.getElementById("display_name").textContent = "@" + user.display_name;
    // document.getElementById("spotify_id").textContent = user.spotify_id;
    // document.getElementById("country").textContent = user.country;
    // document.getElementById("follower_count").textContent = user.follower_count;
    var url = "https://open.spotify.com/user/" + user.spotify_id;
    document.getElementById("sp_profile_url").onclick = function() {window.open(url);};
    // document.getElementById("product").textContent = user.product;
    // document.getElementById("image").src = user.image;

    // Log out button functionality
    document.getElementById("logout").addEventListener("click", function() {
        localStorage.clear();
        window.location.href = "/logout";
    });
});