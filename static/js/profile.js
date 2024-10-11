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


    document.getElementById("displayName").textContent = "@" + user.display_name;
    // document.getElementById("spotify_id").textContent = user.spotify_id;
    // document.getElementById("country").textContent = user.country;
    // document.getElementById("follower_count").textContent = user.follower_count;
    var url = "https://open.spotify.com/user/" + user.spotify_id;
    document.getElementById("spProfileUrl").onclick = function() {window.open(url);};


});