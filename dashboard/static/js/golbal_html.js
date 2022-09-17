const _ID_LIST = ["name", "animate_type", "premiere_date", "author", "official_website", "remarks", "synopsis"]

function show_page(page) {
    let page_list = document.querySelectorAll("#info > div.page");
    for (let i = 0; i < page_list.length; i++) {
        let page = page_list[i];
        if (page.className.includes(page)) {
            page.style["display"] = "";
        }
        else {
            page.style["display"] = "none";
        }
    }
    document.querySelector("#info > div.page." + page).style.display = "";
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
        window.location.hash = "#info"
        send_keyword(element.value);
    }
}

function send_keyword(keyword) {
    show_page("loading");
    let xhttp = new XMLHttpRequest();
    let data = {
        "keyword": keyword
    }
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
            try {
                let raw_data = JSON.parse(this.responseText);
                let animate_data = raw_data["data"];
                if (animate_data == null) {
                    show_page("search");
                    return;
                }
                if (raw_data["type"] == "url") {
                    for (let i = 0; i < _ID_LIST.length; i++) {
                        document.getElementById("info_" + _ID_LIST[i]).textContent = animate_data[_ID_LIST[i]];
                        if (_ID_LIST[i] == "official_website") {
                            document.getElementById("info_" + _ID_LIST[i]).href = animate_data[_ID_LIST[i]];
                        }
                    }
                    show_page("data");
                }
                else {
                    let results = document.getElementById("search_results");
                    for (let i = 0; i < animate_data.length; i++) {
                        let result_box = createElement("div", {className: "result_box"});
                        let raw_title = animate_data[i]["title"];
                        let title_1 = raw_titl
                        let url = animate_data[i]["url"];
                        result_box.appendChild(createElement("p", {className: "cfont", textContent: }));
                    }
                }
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