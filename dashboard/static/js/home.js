function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function home_onload() {
    update_queue();
    setInterval(update_queue, 3000);
    include_try();
}

async function include_try(){
    let finish = false;
    while (!finish) {
        try {
            document.getElementById('top_bar_search_box').onkeydown = function(e){if (e.key=='Enter'){console.log('Enter!!');}};
            finish = true;
        }
        catch {
            await sleep(1000);
        }
    }
}

function createElement(el, options={}){
    let element = document.createElement(el);
    Object.keys(options).forEach(function (k){
       element[k] = options[k];
    });
    return element;
}

async function update_queue() {
    let response = await fetch(document.location.origin + "/api/v1.0/queue");
    let data = JSON.parse(await response.text());
    for (let i = 0; i < data.length; i++) {
        let info = data[i];
        let id = info.id;
        let name = info.name;
        let progress = info.progress;
        if (document.querySelector(`#${id}`) == null) {
            let progress_bar = createElement("div", {className: "progress_bar", id: id});

            let progress_title = createElement("div", {className: "progress_title"});
            progress_title.appendChild(createElement("p", {className: "cfont", textContent: name}));
            progress_title.appendChild(createElement("div", {className: "empty"}));
            progress_title.appendChild(createElement("p", {className: "present cfont", textContent: `${progress}%`}));

            let progress_e = createElement("div", {className: "progress"});
            progress_e.appendChild(createElement("div", {className: "in"}));

            progress_bar.appendChild(progress_title);
            progress_bar.appendChild(progress_e);

            document.querySelector(".queue").appendChild(progress_bar);
        }
        document.querySelector(`#${id} > div.progress_title > p.present.cfont`).textContent = `${progress}%`;
        document.querySelector(`#${id} > div.progress > div`).style.width = `${progress}%`;
    }
}

function send_setting() {
    xhttp = new XMLHttpRequest();
    data
}
