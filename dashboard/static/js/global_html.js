const _ID_LIST = ["url", "name", "animate_type", "premiere_date", "author", "official_website", "remarks", "synopsis", "episode_number"]

// 創造元素
function createElement(el, options={}){
    let element = document.createElement(el);
    Object.keys(options).forEach(function (k){
       element[k] = options[k];
    });
    return element;
}
