function set_water_on() {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
         if (this.readyState == 4 && this.status == 200) {
             alert(this.responseText);
         }
    };
    xhttp.open("GET", "localhost/water_on", true);
    // xhttp.setRequestHeader("Content-type", "application/json");
    // xhttp.send("Your JSON Data Here");
}