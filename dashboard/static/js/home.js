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
    get_queue();
    setInterval(get_queue, 3000);
    get_setting();
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
    xhttp.setRequestHeader("Request-type", "get_queue");
    xhttp.send(JSON.stringify(data));
}

function update_queue(raw_data) {
    let sort_list = raw_data["sort_list"];
    let data = raw_data["data"];
    for (let i = 0; i < sort_list.length; i++) {
        let uuid = sort_list[i];
        let info = data[uuid]
        let name = info.name;
        let progress = info.progress;
        let status = info.status;
        let fail = info.fail;
        let order = info.order;
        if (document.querySelector(`#${uuid}`) == null) {
            if (status == "finish" && !fail) {
                continue;
            }
            let progress_bar = gen_progress_bar(uuid, name, progress);
            document.querySelector(".queue").appendChild(progress_bar);
        }
        document.querySelector(`#${uuid} > div.progress_title > p.present.cfont`).textContent = `${progress}%`;
        document.querySelector(`#${uuid} > div.progress > div`).style.width = `${progress}%`;
        document.querySelector(`#${uuid}`).style.order = order;
        let title_element = document.querySelector(`#${uuid} > div.progress_title > p.cfont`);
        if (fail) {
            title_element.textContent = name + " - 下載失敗";
            document.querySelectorAll(`#${uuid} > div.progress_title > button`).forEach((e)=>{
                e.disabled = true;
            })
            return;
        }
        switch (status) {
            case "unstart":
                title_element.textContent = name + " - 等待中";
                document.querySelectorAll(`#${uuid} > div.progress_title > button`)[2].disabled = true;
                document.querySelectorAll(`#${uuid} > div.progress_title > button`)[3].disabled = true;
                break;
            case "cancel":
                title_element.textContent = name + " - 取消";
                document.querySelectorAll(`#${uuid} > div.progress_title > button`).forEach((e)=>{
                    e.disabled = true;
                })
                break;
            case "pause":
                title_element.textContent = name + " - 暫停中";
                document.querySelectorAll(`#${uuid} > div.progress_title > button`)[2].textContent = "play_arrow";
                break;
            case "finish":
                title_element.textContent = name + " - 完成";
                document.querySelectorAll(`#${uuid} > div.progress_title > button`).forEach((e)=>{
                    e.disabled = true;
                })
                break;
            case "running":
                title_element.textContent = name;
                document.querySelectorAll(`#${uuid} > div.progress_title > button`)[2].textContent = "pause";
                document.querySelectorAll(`#${uuid} > div.progress_title > button`).forEach((e)=>{
                    e.disabled = false;
                })
                break;
        }
    }
}
function sned_queue_action(event) {
    let element = event.target;
    let uuid = element.parentElement.parentElement.id;
    let shift = event.shiftKey;
    let action = "move", target_index = null;
    element.parentElement.querySelectorAll("button").forEach((e)=>{
        e.disabled = true;
    })
    switch (element.textContent) {
        case "arrow_drop_up":
            target_index = "+";
            if (shift) {target_index = "top";}
            break;
        case "arrow_drop_down":
            target_index = "-";
            if (shift) {target_index = "bottom";}
            break;
        case "play_arrow":
            action = "resume";
            break;
        case "pause":
            action = "pause";
            break;
        case "stop":
            action = "cancel";
            break;
    }
    let xhttp = new XMLHttpRequest();
    let data = {
        "uuid": uuid,
        "action": action,
        "target_index": target_index
    }
    xhttp.open("POST", "/", true);
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
            let raw_data = JSON.parse(this.responseText);
            update_queue(raw_data);
            element.parentElement.querySelectorAll("button").forEach((e)=>{
                e.disabled = false;
            })
            if (action == "pause") {
                element.textContent = "play_arrow";
            }
            else if (action == "resume") {
                element.textContent = "pause"
            }
        }
    }
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.setRequestHeader("Request-type", "queue_action");
    xhttp.send(JSON.stringify(data));
}
function gen_progress_bar(uuid, name, progress) {
    let progress_bar = createElement("div", {className: "progress_bar", id: uuid});

    let progress_title = createElement("div", {className: "progress_title"});
    progress_title.appendChild(createElement("p", {className: "cfont", textContent: name, title: name}));
    progress_title.appendChild(createElement("div", {className: "empty"}));
    progress_title.appendChild(
        createElement("button", {
            className: "material-icons",
            textContent: "arrow_drop_up",
            onclick: sned_queue_action
        })
    );
    progress_title.appendChild(
        createElement("button", {
            className: "material-icons",
            textContent: "arrow_drop_down",
            onclick: sned_queue_action
        })
    );
    progress_title.appendChild(
        createElement("button", {
            className: "material-icons",
            textContent: "play_arrow",
            onclick: sned_queue_action
        })
    );
    progress_title.appendChild(
        createElement("button", {
            className: "material-icons",
            textContent: "stop",
            onclick: sned_queue_action
        })
    );
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