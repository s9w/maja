document.addEventListener("DOMContentLoaded", function(){
  // var now = moment();

  var yday = moment().subtract(1, 'days');
  var readElArray = document.getElementsByTagName("ul");
    for(var i = readElArray.length-1; i>=0; i--){
        var ulElement = readElArray[i];
        for(var j = 0; j < ulElement.children.length; j++){
            var liElement = ulElement.children[j];
            var mom = moment.unix(liElement.dataset.date);

            if(mom.isBefore(yday)){
                // Looks silly before first element. In that case: no indication at all
                if(j===0){
                    break;
                }

                liElement.classList.add("time_24h_margin");

                var newNode = document.createElement("div");
                newNode.appendChild(document.createTextNode("↓ 24 hours ↓"));
                newNode.classList.add("time_24h");
                // ulElement.insertBefore(newNode, liElement);
                liElement.appendChild(newNode);
                break;
            }

            // console.log("li, " + readElArray[i].children[j].dataset.date);
        }
    }
});

function mark_read(el, category_id, timestamp){
    for(var li = el.parentElement; li; li=li.nextElementSibling){
        li.classList.add("read");
    }

    var url = "mark_read?timestamp=" + timestamp + "&cat_id=" + category_id;
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

function vac(){
    var url = "vacuum";
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
    for(var li = el.parentElement; li; li=li.nextElementSibling){
        li.classList.remove("read_temp");
    }
}
