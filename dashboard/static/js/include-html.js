function includeHTML() {
    var z, i, elmnt, file, xhttp, data;
    /* Loop through a collection of all HTML elements: */
    z = document.getElementsByTagName("*");
    for (i = 0; i < z.length; i++) {
        elmnt = z[i];
        /*search for elements with a certain atrribute:*/
        file = elmnt.getAttribute("include-html");
        if (file) {
            /* Make an HTTP request using the attribute value as the file name: */
            xhttp = new XMLHttpRequest();
            data = {
                "file_name": file.toString()
            }
            xhttp.onreadystatechange = function() {
            if (this.readyState == 4) {
                if (this.status == 404) {elmnt.innerHTML = "Page not found.";}
                else {elmnt.innerHTML = this.responseText;}
                /* Remove the attribute, and call this function once more: */
                elmnt.removeAttribute("include-html");
                includeHTML();
            }
            }
            xhttp.open("POST", "/", true);
            xhttp.setRequestHeader("Content-type", "application/json");
            xhttp.setRequestHeader("Request-type", "include");
            xhttp.send(JSON.stringify(data));
            /* Exit the function: */
            return;
        }
    }
}