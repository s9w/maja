document.addEventListener("DOMContentLoaded", function(){
    function getSeparationString (dayPeriod) {
        var day_str = dayPeriod===1?"day":"days";
        return "↓ " + dayPeriod + " "+day_str+" ↓"
    }

  var lists = document.getElementsByTagName("ul");
    for(var i_list = lists.length-1; i_list>=0; i_list--){
        var ulElement = lists[i_list];

        var dayPeriod = 1;

        for(var j = 0; j < ulElement.children.length; j++){
            var liElement = ulElement.children[j];
            var mom = moment.unix(liElement.dataset.date);
            var day = moment().subtract(dayPeriod, 'days');

            if(mom.isBefore(day)){
                // Skip time period indication at first element (looks silly)
                if(j===0){
                    dayPeriod += 1;
                    continue;
                }

                // Mark post as first in new day period
                liElement.classList.add("day_separation");

                // Add horizontal line as visual divider
                var newNode = document.createElement("div");
                newNode.appendChild(document.createTextNode(getSeparationString(dayPeriod)));
                newNode.classList.add("day_indicator");
                liElement.appendChild(newNode);

                dayPeriod += 1;
            }
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
