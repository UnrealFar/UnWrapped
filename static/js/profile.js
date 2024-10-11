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


    const profileImage = document.getElementById('profileImage');
    const profileCard = document.getElementsByClassName('card')[0];
    const colorThief = new ColorThief();

    profileImage.crossOrigin = 'Anonymous';
    profileImage.onload = () => {
        const color = colorThief.getColor(profileImage);
        const tdcolor = color.map(channel => Math.floor(channel * 0.7 + 255 * 0.3));
        const tdcolorRgb = `rgb(${tdcolor[0]}, ${tdcolor[1]}, ${tdcolor[2]})`;
        profileCard.style.background = `linear-gradient(to bottom, ${tdcolorRgb} 60%, black)`;
    };

    if (profileImage.complete) {
        profileImage.onload()
    }

});