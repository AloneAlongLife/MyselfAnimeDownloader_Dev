// 切換分頁
function show_page(page_name) {
    let page_list = document.querySelectorAll("#info > div.page");
    for (let i = 0; i < page_list.length; i++) {
        let page = page_list[i];
        if (page.className.includes(page_name)) {
            page.style["display"] = "";
        }
        else {
            page.style["display"] = "none";
        }
    }
}


// 搜尋
function search_keydown(element, e) {
    if (e.key=='Enter') {
        if (element.value == "") {return;}
        show_page("loading");
        window.location.hash = "#info"
        send_keyword(element.value);
        element.value = "";
    }
}

// 發送關鍵字
function send_keyword(keyword, from_cache=true, from=null) {
    let xhttp = new XMLHttpRequest();
    let data;
    if (from == null) {
        data = {
            "keyword": keyword,
            "cache": from_cache,
            "from": get_source().toLowerCase()
        }
    }
    else {
        data = {
            "keyword": keyword,
            "cache": from_cache,
            "from": from
        }
    }
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
            try {
                let raw_data = JSON.parse(this.responseText);
                update_animate_info(raw_data);
            }
            catch {
                show_page("search");
            }
        }
    }
    xhttp.open("POST", "/", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.setRequestHeader("Request-type", "animate_info");
    xhttp.send(JSON.stringify(data));
}

// 更新搜尋列表
function update_animate_info(raw_data) {
    let animate_data = raw_data["data"];
    if (animate_data == null) {
        show_page("search");
        return;
    }
    if (raw_data["type"] == "url") {
        if (raw_data["from"] == "myself") {
            for (let i = 0; i < _ID_LIST.length; i++) {
                document.getElementById("info_" + _ID_LIST[i]).textContent = animate_data[_ID_LIST[i]];
                if (_ID_LIST[i] == "official_website" || _ID_LIST[i] == "url") {
                    document.getElementById("info_" + _ID_LIST[i]).href = animate_data[_ID_LIST[i]];
                }
            }
            document.getElementById("info_img").src = `/cache/img?url=${encodeURI(animate_data["image"])}`;
            show_page("data");

            update_episode_queue(raw_data);
        }
        else if (raw_data["from"] == "anime1") {
            for (let i = 0; i < _ID_LIST.length; i++) {
                document.getElementById("info_" + _ID_LIST[i]).textContent = animate_data[_ID_LIST[i]];
                if (_ID_LIST[i] == "official_website" || _ID_LIST[i] == "url") {
                    document.getElementById("info_" + _ID_LIST[i]).href = animate_data[_ID_LIST[i]];
                }
            }
            document.getElementById("info_img").src = "../static/img/blank.jpg";
            show_page("data");

            update_episode_queue(raw_data, false);
        }
    }
    else {
        let results = document.getElementById("search_results");
        results.innerHTML = "";
        for (let i = 0; i < animate_data.length; i++) {
            let result_box = createElement("div", {className: "result_box"});
            let raw_title = animate_data[i]["title"];
            let url = animate_data[i]["url"];
            let index = raw_title.indexOf("【");
            if (index != -1 || raw_data["from"] == "anime1") {
                let p_element;
                if (index == -1) {
                    p_element = createElement("p", {className: "cfont", textContent: raw_title});
                }
                else {
                    p_element = createElement("p", {className: "cfont", textContent: raw_title.slice(0, index)});
                }
                // if (p_element.textContent.length > 20){
                //     p_element.style["font-size"] = `${parseInt(240 / p_element.textContent.length) + 1}px`;
                // }
                p_element.style["font-size"] = "auto";
                result_box.appendChild(p_element);
                if (raw_data["from"] == "myself") {
                    result_box.appendChild(createElement("p", {className: "cfont", textContent: raw_title.slice(index)}));
                }
                result_box.onclick = function() {
                    send_keyword(url, from=raw_data["from"]);
                    show_page("loading");
                };
                results.appendChild(result_box);
            }
            else {
                // let p_element = createElement("p", {className: "cfont", textContent: raw_title});
                // if (p_element.textContent.length > 20){
                //     p_element.style["font-size"] = `${parseInt(386 / p_element.textContent.length) + 1}px`;
                // }
                // result_box.appendChild(p_element);
            }
            // result_box.onclick = function() {
            //     show_page("loading");
            //     send_keyword(url);
            // };
            // results.appendChild(result_box);
        }
        if (animate_data.length == 0) {
            show_page("search");
        }
        else {
            show_page("results");
        }
    }
}

// 更新集數列表
function update_episode_queue(raw_data, check_episode=true) {
    document.querySelector("div.episode_page.episode_loading").style["display"] = "";
    document.querySelector("div.episode_page.episode_content").style["display"] = "none";

    let data = raw_data["data"]

    if (raw_data["from"] != "myself") {
        check_episode = false;
    }

    if (check_episode) {
        let episode_num_check = `全 ${data["episode_data"].length} 話`;
        if (episode_num_check != data["episode_number"]) {
            let xhttp = new XMLHttpRequest();
            let send_data = {
                "keyword": data["url"],
                "cache": false,
                "from": raw_data["from"]
            }
            xhttp.onreadystatechange = function() {
                if (this.readyState == 4) {
                    try {
                        let raw_data = JSON.parse(this.responseText);
                        update_episode_queue(raw_data, false);
                    }
                    catch {
                        show_page("search");
                    }
                }
            }
            xhttp.open("POST", "/", true);
            xhttp.setRequestHeader("Content-type", "application/json");
            xhttp.setRequestHeader("Request-type", "animate_info");
            xhttp.send(JSON.stringify(send_data));
        }
        else {
            check_episode = false;
        }
    }

    let queue_element = document.querySelector("div.episode_queue");
    queue_element.innerHTML = ""
    last_select_episode = 1;
    for (let i = 0; i < data["episode_data"].length; i++) {
        let episode_box = createElement("div", {className: "episode_box"})
        episode_box.appendChild(createElement("p", {className: "cfont", textContent: data["episode_data"][i]["name"]}));
        let check_box = createElement("input", {className: "cfont", type: "checkbox", value: data["episode_data"][i]["url"]})
        check_box.onclick = function (event) {
            if (event.shiftKey) {
                if (last_select_episode >= i + 1) {
                    select(`!${last_select_episode}-${i + 1}`);
                }
                else {
                    select(`${last_select_episode}-${i + 1}`);
                }
            }
            last_select_episode = i + 1;
        }
        episode_box.appendChild(check_box);
        queue_element.appendChild(episode_box);
    }
    console.log(check_episode)

    if (!check_episode) {
        document.querySelector("div.episode_page.episode_content").style["display"] = "";
        document.querySelector("div.episode_page.episode_loading").style["display"] = "none";
    }
}

function update_source (element) {
    let parent = document.querySelectorAll(".source-selector");
    parent.forEach((parent_element)=>{
        parent_element.querySelectorAll("button").forEach((button_element)=>{
            if (button_element.textContent == element.textContent) {
                button_element.classList.add("source-selected");
            }
            else {
                button_element.classList.remove("source-selected");
            }
        })
    })
}

function get_source () {
    let parent = document.querySelector(".source-selector");
    let answer = "Myself"
    parent.querySelectorAll("button").forEach((button_element)=>{
        if (button_element.className.search("source-selected") != -1) {
            answer = button_element.textContent;
        }
    })
    return answer;
}