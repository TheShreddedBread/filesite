function filter(elem) {
    var search = document.getElementById("storageSearch").value;
    filterFilesFromText(search)
}

function filterFilesFromText(search) {
    var items = document.getElementsByClassName("uploadedFile");
    for (let i = 0; i < items.length; i++) {
        var filename = items[i].getElementsByClassName("filename")[0].textContent;
        if (filename.toLowerCase().includes(search.toLowerCase()) || search.length == 0) {
            items[i].hidden = false;
        } else {
            items[i].hidden = true;
        }
    }
    
    setTimeout( function() { document.getElementById("searchDropdown").style = "display: none;"; }, 500);
    
}

function openFileMenu(elem) {
    elem.parentElement.hidden = true;
    var optionElem = elem.parentElement.parentElement.parentElement.getElementsByClassName("squarepage2")[0]
    optionElem.hidden = false;
    optionElem.getElementsByClassName("fileOptions")[0].hidden = false;
}

function closeFileMenu(elem) {
    elem.parentElement.hidden = true;
    var optionElem = elem.parentElement.parentElement.parentElement.getElementsByClassName("squarepage2")[0]
    var defaultpage = elem.parentElement.parentElement.parentElement.getElementsByClassName("squarepage1")[0]
    optionElem.hidden = true;
    defaultpage.getElementsByClassName("fileOptions")[0].hidden = false;
}

function closeAllFileOptionMenu(elem) {
    var elems = elem.getElementsByClassName("uploadedFile");
    for (let i = 0; i < elems.length; i++) {
        elems[i].getElementsByClassName("squarepage2")[0].hidden = true;
        var squarep1 = elems[i].getElementsByClassName("squarepage1")[0];
        squarep1.getElementsByClassName("fileOptions")[0].hidden = false;
    }
}

function alertFileInfo(elem) {
    alert(`Name: ${elem.parentElement.parentElement.parentElement.getElementsByClassName("fileName")[0].textContent}\nSize: ${elem.parentElement.parentElement.parentElement.getElementsByClassName("fileSize")[0].textContent}`);
}

function updatePreviewName(elem) {
    var fileName = elem.files[0].name;
    if(fileName.length != 0) {
        document.getElementById("filename").innerHTML = "Selected File: " + fileName;
    }
}

function addUser(elem) {
    var newMail = document.getElementById("newusermail").value;
    if (newMail.length > 0) {
        if (!newMail.includes("@")) {
            alert("Please input a valid email");
            return;
        }
        var base = document.createElement("div");
        base.classList.add("mailitem");

        var mailtag = document.createElement("span");
        mailtag.textContent = newMail;

        var storeMail = document.createElement("input");
        storeMail.hidden = true;
        storeMail.name = "addedmail";
        storeMail.value = newMail;
    
        var removeBtn = document.createElement("button");
        removeBtn.setAttribute("onclick", "deleteUser(this)");
        
        var removeIcon = document.createElement("span");
        removeIcon.classList.add("material-symbols-outlined");
        removeIcon.textContent = "person_remove";

        removeBtn.appendChild(removeIcon);

        base.appendChild(mailtag);
        base.appendChild(storeMail);
        base.appendChild(removeBtn);

        document.getElementById("maillist").appendChild(base);
    }
}

function deleteUser(elem) {
    elem.parentElement.remove();
}

function submitForm(id) {
    document.getElementById(id).submit();
}

var searchDropdownItems = new Array();

function filterWithDropdown(pos) {
    if (pos < searchDropdownItems.length && pos >= 0) {
        updateMatchesFromText(searchDropdownItems[pos][0]);
        document.getElementById("storageSearch").value = searchDropdownItems[pos][0];
        filterFilesFromText(searchDropdownItems[pos][0]);
    }
}

function updateMatches(elem) {
    updateMatchesFromText(elem.value)
}

function updateMatchesFromText(text) {
    searchDropdownItems = new Array();
    document.getElementById("searchDropdown").innerHTML = ""

    var itemsFound = false;
    var items = document.getElementsByClassName("uploadedFile");
    var counter = 0;
    for (let i = 0; i < items.length; i++) {
        var filename = items[i].getElementsByClassName("filename")[0].textContent;
        if (filename.toLowerCase().includes(text.toLowerCase()) || text.length == 0) {
            itemsFound = true;

            var base = document.createElement("div");
            base.classList.add("searchItem");
            searchDropdownItems.push([filename, i]);
            base.setAttribute("onclick", `filterWithDropdown(${counter})`);
            counter++;

            var suggestedFileName = document.createElement("a");
            suggestedFileName.textContent = filename;
            base.appendChild(suggestedFileName);

            document.getElementById("searchDropdown").appendChild(base);
        }
    }

    if (!itemsFound) {
        document.getElementById("searchDropdown").textContent = "No items found"
    }

    if (text.length == 0) {
        document.getElementById("searchDropdown").style = "display: none;";
    } else {
        document.getElementById("searchDropdown").style = "";
    }
}

var hoverOverFile = [false,-1]
if (document.addEventListener) {
    var files = document.getElementsByClassName("uploadedFile");
    for(let i = 0; i < files.length; i++) {
        files[i].onmouseenter = function() {hoverOverFile = [true, i];}
        files[i].onmouseleave = function() {hoverOverFile = [false, -2];}
        // files[i].contextmenu = function() {alert("alr")}
    }
    document.addEventListener('contextmenu', function(e) {
        if (hoverOverFile[0]) {
            openFileOptions();
        }
        e.preventDefault();
    }, false);
    } else {
    document.attachEvent('oncontextmenu', function() {
        if (hoverOverFile[0]) {
            openFileOptions();
        }
        window.event.returnValue = false;
    });
} 

function closeAlert(elem) {
    elem.parentElement.parentElement.remove()
}

function openFileOptions() {
    openFileMenu(document.getElementsByClassName("uploadedFile")[hoverOverFile[1]].getElementsByClassName("openFileOptionsBtn")[0].getElementsByClassName("material-symbols-outlined")[0]);
}

function StopEventPropagation(event) {
    if (event.stopPropagation) {
        event.stopPropagation();
    }
    else if (window.event) {
        window.event.cancelBubble = true;
    }
}     

if ( window.history.replaceState ) {
    window.history.replaceState( null, null, window.location.href );
}