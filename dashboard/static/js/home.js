function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function show_setting(page_name) {
    let page_list = document.querySelectorAll("#setting_form > div.setting_card");
    for (let i = 0; i < page_list.length; i++) {
        let page = page_list[i];
        if (page.id == page_name) {
            page.style["display"] = "";
        }
        else {
            page.style["display"] = "none";
        }
    }
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

function get_queue() {
    let xhttp = new XMLHttpRequest();
    let data = {}
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
            let raw_data = JSON.parse(this.responseText);
            update_queue(raw_data);
        }
    }
    xhttp.open("POST", "/", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.setRequestHeader("Request-type", "send_setting_form");
    xhttp.send(JSON.stringify(data));
}

async function update_queue(raw_data) {
    try {
        let sort_list = raw_data["sort_list"];
        let data = raw_data["data"];
        for (let i = 0; i < sort_list.length; i++) {
            let uuid = sort_list[i];
            let info = data[uuid]
            let name = info.name;
            let progress = info.progress;
            let status = info.status;
            let fail = info.fail;
            if (document.querySelector(`#${id}`) == null) {
                if (status == "finish") {
                    continue;
                }
                let progress_bar = gen_progress_bar();
                document.querySelector(".queue").appendChild(progress_bar);
            }
            document.querySelector(`#${id} > div.progress_title > p.present.cfont`).textContent = `${progress}%`;
            document.querySelector(`#${id} > div.progress > div`).style.width = `${progress}%`;
        }
    }
    catch {}
}
function gen_progress_bar(id, name, progress) {
    let progress_bar = createElement("div", {className: "progress_bar", id: id});

    let progress_title = createElement("div", {className: "progress_title"});
    progress_title.appendChild(createElement("p", {className: "cfont", textContent: name}));
    progress_title.appendChild(createElement("div", {className: "empty"}));
    progress_title.appendChild(createElement("button", {className: "material-icons upper", textContent: "arrow_drop_up"}));
    progress_title.appendChild(createElement("button", {className: "material-icons lower", textContent: "arrow_drop_down"}));
    progress_title.appendChild(createElement("button", {className: "material-icons pause", textContent: "pause"}));
    progress_title.appendChild(createElement("button", {className: "material-icons stop", textContent: "stop"}));
    progress_title.appendChild(createElement("p", {className: "present cfont", textContent: `${progress}%`}));

    let progress_e = createElement("div", {className: "progress"});
    progress_e.appendChild(createElement("div", {className: "in"}));

    progress_bar.appendChild(progress_title);
    progress_bar.appendChild(progress_e);

    return progress_bar
}

function send_setting() {
    let xhttp = new XMLHttpRequest();
    let data = {}
    let setting_list = document.getElementById("setting_form").getElementsByClassName("info_card");
    for (let i = 0; i < setting_list.length; i++) {
        let input_list = setting_list[i].getElementsByTagName("input")
        let temp_data = {};
        for (let j = 0; j < input_list.length; j++) {
            let value = input_list[j].value;
            if (value == "") {
                value = null;
            }
            else if (input_list[j].type == "checkbox") {
                value = input_list[j].checked;
            }
            temp_data[input_list[j].name] = value;
        }
        data[setting_list[i].id] = temp_data;
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
            update_setting_form(data);
        };
    }
    xhttp.open("POST", "/", true);
    xhttp.setRequestHeader("Content-type", "text");
    xhttp.setRequestHeader("Request-type", "get_setting_form");
    xhttp.send();
}

function update_setting_form(data) {
    // try {
        let setting_list = document.getElementById("setting_form").getElementsByClassName("info_card");
        for (let i = 0; i < setting_list.length; i++) {
            let input_list = setting_list[i].getElementsByTagName("input")
            let temp_data = JSON.parse(data[setting_list[i].id]);
            for (let j = 0; j < input_list.length; j++) {
                if (input_list[j].type == "checkbox") {
                    input_list[j].checked = temp_data[input_list[j].name];
                }
                else {
                    input_list[j].value = temp_data[input_list[j].name];
                }
            }
        }
    // }
    // catch {
    //     setTimeout(()=>{update_setting_form(data);}, 1000);
    // }
}