function mark_read(el, type, subtype, timestamp){
    for(var li = el.parentElement; li; li=li.nextElementSibling){
        li.classList.add("read");
    }

    var url = "mark_read?timestamp=" + timestamp + "&type=" + type + "&subtype=" + subtype;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.send();
    return false;
}

function start_scrape(){
    var url = "scrape";
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.send();
    return false;
}

// marks all posts below as marked_read
function mark_read_temp(el){
    for(var li = el.parentElement; li; li=li.nextElementSibling){
        li.classList.add("read_temp");
    }
}

// undos the read marking
function undo_mark_read_temp(el){
    var readElArray = document.getElementsByClassName("read_temp");
    for(var i = readElArray.length-1; i>=0; i--){
        readElArray[i].classList.remove("read_temp");
    }
}
