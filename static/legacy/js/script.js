function filter(elem) {
    var search = document.getElementById("storageSearch").value;
    var items = document.getElementsByClassName("uploadedFile");
    for (let i = 0; i < items.length; i++) {
        var filename = items[i].getElementsByClassName("filename")[0].textContent;
        if (filename.toLowerCase().includes(search.toLowerCase()) || search.length == 0) {
            items[i].hidden = false;
        } else {
            items[i].hidden = true;
        }
    }
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

function alerFileInfo(elem) {
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

// if (document.addEventListener) {
//     document.addEventListener('contextmenu', function(e) {
//         alert("You've tried to open context menu"); //here you draw your own menu
//         e.preventDefault();
//     }, false);
//     } else {
//     document.attachEvent('oncontextmenu', function() {
//         alert("You've tried to open context menu");
//         window.event.returnValue = false;
//     });
// } 

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