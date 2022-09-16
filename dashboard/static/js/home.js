function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function home_onload() {
    update_queue();
    setInterval(update_queue, 3000);
    get_setting();
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
    let xhttp = new XMLHttpRequest();
    let data = {}
    let input_list = document.getElementById("setting_form").getElementsByTagName("input");
    for (let i = 0; i < input_list.length; i++) {
        let value = input_list[i].value;
        if (value == "") {
            value = null;
        }
        else if (input_list[i].type == "checkbox") {
            value = input_list[i].checked;
        }
        data[input_list[i].name] = value;
    }
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
            get_setting();
        }
    }
    xhttp.open("POST", "/", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.setRequestHeader("Request-type", "send_setting_form");
    xhttp.send(JSON.stringify(data));
}

function get_setting() {
    let xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
            let data = JSON.parse(this.responseText);
            let input_list = document.getElementById("setting_form").getElementsByTagName("input");
            for (let i = 0; i < input_list.length; i++) {
                if (input_list[i].type == "checkbox") {
                    input_list[i].checked = data[input_list[i].name];
                }
                else {
                    input_list[i].value = data[input_list[i].name];
                }
            }
        }
    }
    xhttp.open("POST", "/", true);
    xhttp.setRequestHeader("Content-type", "text");
    xhttp.setRequestHeader("Request-type", "get_setting_form");
    xhttp.send();
}
