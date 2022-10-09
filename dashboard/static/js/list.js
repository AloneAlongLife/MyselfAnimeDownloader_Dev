function list_onload() {
    request_list();
}

// 切換分頁
function show_list(element, page_name) {
    document.querySelectorAll("#list > ih.list").forEach((list)=>{
        if (list.className.includes(page_name)) {
            list.style["display"] = "";
        }
        else {
            list.style["display"] = "none";
        }
    });
    element.classList.add("selected");
    document.querySelectorAll("#list > div.button-box > button").forEach((button)=>{
        if (!button.className.includes(page_name)) {
            button.classList.remove("selected");
        }
    })
}

// 發出請求
function request_list() {
    let xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
            let raw_data = JSON.parse(this.responseText);
            update_list(raw_data);
        }
    }
    xhttp.open("POST", "/", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.setRequestHeader("Request-type", "week_animate");
    xhttp.send(JSON.stringify({}));
}

// 更新列表
function update_list(data) {
    try {
        Object.keys(data).forEach((key)=>{
            let animate_data = data[key];
            let out_link = key == "ani-gamer";
            let today = new Date().getDay() - 1
            if (today == -1) {today = 6;}
            document.querySelectorAll(`#list > ih.list.${key} > .week-day`).forEach((element, index)=>{
                if (animate_data[index].length == 0){
                    element.querySelector(".no-ani").style.display = "";
                }
                else {
                    for (let i = 0; i < animate_data[index].length; i++) {
                        element.appendChild(gen_animeat_block(animate_data[index][i], out_link));
                        if (i < animate_data[index].length - 1) {
                            element.appendChild(createElement("hr", {className: "ani-hr"}));
                        }
                    }
                }
                if (index == today) {
                    element.classList.add("today");
                }
                else {
                    element.classList.remove("today");
                }
            })
        })
    }
    catch {
        setTimeout(update_list, 50, data);
    }
}

// 創造動畫資訊方塊
function gen_animeat_block(data, out_link=false) {
    let basic_element;

    if (out_link) {
        basic_element = createElement("div", {
            className: "ani-block",
            onclick: function () {
                window.open(data["url"], "_blank");
            }
        })
    }
    else {
        let selected = document.querySelector("#list > .list:not([style*='none'])").classList[1];
        basic_element = createElement("div", {
            className: "ani-block",
            onclick: function () {
                show_page("loading");
                window.location.hash = "#info";
                send_keyword(data["url"], true, selected);
            }
        })
    }

    basic_element.appendChild(createElement("p", {
        className: "cfont title",
        textContent: data["name"]
    }));
    basic_element.appendChild(createElement("p", {
        className: "cfont update",
        textContent: data["update"]
    }));

    return basic_element;
}
