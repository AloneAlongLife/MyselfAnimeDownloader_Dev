const _ID_LIST = ["url", "name", "animate_type", "premiere_date", "author", "official_website", "remarks", "synopsis", "episode_number"]

function createElement(el, options={}){
    let element = document.createElement(el);
    Object.keys(options).forEach(function (k){
       element[k] = options[k];
    });
    return element;
}

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

function createElement(el, options={}){
    let element = document.createElement(el);
    Object.keys(options).forEach(function (k){
       element[k] = options[k];
    });
    return element;
}

function search_keydown(element, e) {
    if (e.key=='Enter') {
        if (element.value == "") {return;}
        show_page("loading");
        window.location.hash = "#info"
        send_keyword(element.value);
        element.value = "";
    }
}

function send_keyword(keyword, from_cache=true) {
    let xhttp = new XMLHttpRequest();
    let data = {
        "keyword": keyword,
        "cache": from_cache
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
    xhttp.open("POST", window.location.pathname + window.location.search, true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.setRequestHeader("Request-type", "animate_info");
    xhttp.send(JSON.stringify(data));
}

function update_animate_info(raw_data) {
    let animate_data = raw_data["data"];
    if (animate_data == null) {
        show_page("search");
        return;
    }
    if (raw_data["type"] == "url") {
        for (let i = 0; i < _ID_LIST.length; i++) {
            document.getElementById("info_" + _ID_LIST[i]).textContent = animate_data[_ID_LIST[i]];
            if (_ID_LIST[i] == "official_website" || _ID_LIST[i] == "url") {
                document.getElementById("info_" + _ID_LIST[i]).href = animate_data[_ID_LIST[i]];
            }
        }
        document.getElementById("info_img").src = `/cache/img?url=${encodeURI(animate_data["image"])}`;
        show_page("data");

        update_episode_queue(animate_data);
    }
    else {
        let results = document.getElementById("search_results");
        results.innerHTML = "";
        for (let i = 0; i < animate_data.length; i++) {
            let result_box = createElement("div", {className: "result_box"});
            let raw_title = animate_data[i]["title"];
            let url = animate_data[i]["url"];
            let index = raw_title.indexOf("【");
            if (index != -1) {
                let p_element = createElement("p", {className: "cfont", textContent: raw_title.slice(0, index)});
                if (p_element.textContent.length > 22){
                    p_element.style["font-size"] = `${parseInt(396 / p_element.textContent.length) + 1}px`;
                }
                result_box.appendChild(p_element);
                result_box.appendChild(createElement("p", {className: "cfont", textContent: raw_title.slice(index)}));
            }
            else {
                let p_element = createElement("p", {className: "cfont", textContent: raw_title});
                if (p_element.textContent.length > 22){
                    p_element.style["font-size"] = `${parseInt(396 / p_element.textContent.length) + 1}px`;
                }
                result_box.appendChild(p_element);
            }
            result_box.onclick = function() {
                show_page("loading");
                send_keyword(url);
            };
            results.appendChild(result_box);
        }
        show_page("results");
    }
}

function update_episode_queue(data, check_episode=true) {
    document.querySelector("div.episode_page.episode_loading").style["display"] = "";
    document.querySelector("div.episode_page.episode_content").style["display"] = "none";

    if (check_episode) {
        let episode_num_check = `全 ${data["episode_data"].length} 話`;
        if (episode_num_check != data["episode_number"]) {
            let xhttp = new XMLHttpRequest();
            let send_data = {
                "keyword": data["url"],
                "cache": false
            }
            xhttp.onreadystatechange = function() {
                if (this.readyState == 4) {
                    try {
                        let raw_data = JSON.parse(this.responseText);
                        let animate_data = raw_data["data"];
                        update_episode_queue(animate_data, false);
                    }
                    catch {
                        show_page("search");
                    }
                }
            }
            xhttp.open("POST", window.location.pathname + window.location.search, true);
            xhttp.setRequestHeader("Content-type", "application/json");
            xhttp.setRequestHeader("Request-type", "animate_info");
            xhttp.send(JSON.stringify(send_data));
            return;
        }
    }

    let queue_element = document.querySelector("div.episode_queue");
    queue_element.innerHTML = ""
    for (let i = 0; i < data["episode_data"].length; i++) {
        let episode_box = createElement("div", {className: "episode_box"})
        episode_box.appendChild(createElement("p", {className: "cfont", textContent: data["episode_data"][i]["name"]}));
        episode_box.appendChild(createElement("input", {className: "cfont", type: "checkbox", value: data["episode_data"][i]["url"]}));
        queue_element.appendChild(episode_box);
    }

    document.querySelector("div.episode_page.episode_content").style["display"] = "";
    document.querySelector("div.episode_page.episode_loading").style["display"] = "none";
}