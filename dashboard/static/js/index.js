function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function index_onload() {
    setInterval(change_ico, 3000);
}

function change_ico() {
    try {
        let icon = document.querySelector("link[rel='icon']");
        let logo = document.querySelector("#top-bar > img");
        if (icon.href.includes("favicon.ico")) {
            icon.href = icon.href.replace("favicon.ico", "favicon2.ico");
            logo.src = logo.src.replace("logo2.png", "logo.png");
        }
        else {
            icon.href = icon.href.replace("favicon2.ico", "favicon.ico");
            logo.src = logo.src.replace("logo.png", "logo2.png");
        }
    }
    catch {}
}

function hash_change() {
    let hash = window.location.hash;
    try {
        if (document.querySelector(hash) == null) {
            window.location.hash = "#home";
        }
    }
    catch {hash = "#home";}
    document.querySelectorAll(".content").forEach((element)=>{
        if (hash == `#${element.id}`) {
            element.style.display = "";
        }
        else {
            element.style.display = "none";
        }
    });
}
