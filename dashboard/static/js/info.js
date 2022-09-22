function select(input) {
    if (input == "all") {
        input = `1-${document.querySelectorAll("div.episode_box > input").length}`;
    }
    else if (input == "none") {
        input = `!1-${document.querySelectorAll("div.episode_box > input").length}`;
    }
    else {
        input = document.querySelector("div.episode_selector > input").value;
        document.querySelector("div.episode_selector > input").value = "";
    }
    input = input.replaceAll(" ", "");
    let select_list = input.split(",")
    for (let i = 0; i < select_list.length; i++) {
        let select_str = select_list[i];
        if (select_str.indexOf("-") != -1) {
            let change_to = true;
            if (select_str[0] == "!") {
                change_to = false;
                select_str = select_str.slice(1);
            }
            select_str = select_str.split("-");
            let start = parseInt(select_str[0]);
            let end = parseInt(select_str[1]);

            let total_episode = document.querySelectorAll("div.episode_box > input");
            let len = total_episode.length;
            if (start < 0) {start = len + start;}
            else {start -= 1;}
            if (start < 0) {start = 0;}

            if (end < 0) {end = len + end + 1;}
            if (end > len) {end = len}

            for (let j = start; j < end; j++) {
                total_episode[j].checked = change_to;
            }
        }
        else {
            let change_to = true;
            if (select_str[0] == "!") {
                change_to = false;
                select_str = select_str.slice(1);
            }
            let index = parseInt(select_str);
            let total_episode = document.querySelectorAll("div.episode_box > input");
            let len = total_episode.length;
            if (index == NaN || index < 1 || index >= len) {return;}
            if (index < 0) {index = len + index;}
            else {index -= 1;}
            total_episode[index].checked = change_to;
        }
    }
}

function send_download_queue() {
    let xhttp = new XMLHttpRequest();
    let data = {}
    data["url"] = document.getElementById("info_url").href;
    data["queue"] = [];
    let queue = document.getElementsByClassName("episode_queue")[0];
    for (let i = 0; i < queue.length; i++) {
        let content_element = queue[i];
        let temp_data = {};
        if (content_element.querySelector("input").checked) {
            temp_data["url"] = content_element.querySelector("input").value;
            temp_data["index"] = content_element.querySelector("p");
        }
    }
    xhttp.open("POST", "/", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.setRequestHeader("Request-type", "send_download_queue");
    xhttp.send(JSON.stringify(data));
}