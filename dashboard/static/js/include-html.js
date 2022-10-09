// function includeHTML() {
//     let z = document.getElementsByTagName("*");
    
//     for (let i = 0; i < z.length; i++) {
//         let elmnt = z[i];
//         let file = elmnt.getAttribute("include-html");
//         if (file) {
//             let xhttp = new XMLHttpRequest();
//             let data = {
//                 "file_name": file.toString()
//             }
//             xhttp.onreadystatechange = function() {
//                 if (this.readyState == 4) {
//                     if (this.status == 404) {elmnt.innerHTML = "Page not found.";}
//                     else {elmnt.innerHTML = this.responseText;}
//                     elmnt.removeAttribute("include-html");
//                 }
//             }
//             xhttp.open("POST", "/", true);
//             xhttp.setRequestHeader("Content-type", "application/json");
//             xhttp.setRequestHeader("Request-type", "include");
//             xhttp.send(JSON.stringify(data));
//         }
//     }
// }

function includeHTML(i=0) {
    let include_list = document.getElementsByTagName("ih");
    if (i >= include_list.length) {
        return
    }
    let element = include_list[i];
    let xhttp = new XMLHttpRequest();
    let data;
    console.log()
    if (element.id == "") {
        data = {
            "file_name": element.getAttribute("include-html") + ".html"
        }
    }
    else {
        data = {
            "file_name": element.id + ".html"
        }
    }
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
            if (this.status == 404) {element.innerHTML = "Page not found.";}
            else {element.innerHTML = this.responseText;}
            setTimeout(includeHTML, 0, i+1)
        }
    }
    xhttp.open("POST", "/", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.setRequestHeader("Request-type", "include");
    xhttp.send(JSON.stringify(data));
}
