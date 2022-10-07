const _ID_LIST = ["url", "name", "animate_type", "premiere_date", "author", "official_website", "remarks", "synopsis", "episode_number"]

// 創造元素
function createElement(el, options={}){
    let element = document.createElement(el);
    Object.keys(options).forEach(function (k){
       element[k] = options[k];
    });
    return element;
}

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
