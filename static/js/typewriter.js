const twtxts = [
    `Do you ever wish you could generate your Spotify Wrapped at any time of the year?
<break:{1}>Well, guess what?`,
`<break:{6}><untype:{0.25}>You</untype><untype:{0.5}> can</untype>!`,
];

document.addEventListener("DOMContentLoaded", function() {

    const typewriterElements = document.querySelectorAll(".typewriter");

    typewriterElements.forEach(element => {
        const id = element.id;
        const index = parseInt(id.replace('twtxt', ''), 10);

        // Check if the index is valid
        if (index >= 0 && index < twtxts.length) {
            const text = twtxts[index];
            element.textContent = "";
            element.style.visibility = "hidden";
            let idx = 0;

            function type() {
                if (idx === 0) {
                    element.style.visibility = "visible";
                }

                // Checks for <break:{time}> tag
                const breakMatch = text.substring(idx).match(/^<break:\{(\d+(\.\d+)?)\}>/);
                if (breakMatch) {
                    const breakTime = parseFloat(breakMatch[1]) * 1000;
                    idx += breakMatch[0].length;
                    setTimeout(type, breakTime);
                    return;
                }

                // Checks for <untype:{delay}>content</untype> tag
                const untypeMatch = text.substring(idx).match(/^<untype:\{(\d+(\.\d+)?)\}>(.*?)<\/untype>/);
                if (untypeMatch) {
                    const untypeDelay = parseFloat(untypeMatch[1]) * 1000;
                    const untypeContent = untypeMatch[3];
                    idx += untypeMatch[0].length;
                    setTimeout(() => {
                        element.innerHTML = element.innerHTML.replace(/<span class="cursor">█<\/span>$/, '') + untypeContent + '<span class="cursor">█</span>';
                        type();
                    }, untypeDelay);
                    return;
                }

                if (idx < text.length) {
                    const nextChar = text[idx];
                    if (nextChar === '<') {
                        const tagEnd = text.indexOf('>', idx);
                        if (tagEnd !== -1) {
                            idx = tagEnd + 1;
                            setTimeout(type, 0);
                            return;
                        }
                    }
                    element.innerHTML = text.substring(0, idx + 1).replace(/<.*?>/g, '') + '<span class="cursor">█</span>';
                    idx++;
                    setTimeout(type, 40);
                } else {
                    element.innerHTML = element.innerHTML.replace(/<span class="cursor">█<\/span>$/, '');
                }
            }

            type();
        } else {
            console.error(`Invalid index ${index} for element with id ${id}`);
        }
    });
});