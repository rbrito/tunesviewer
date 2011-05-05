/*
 * iTunes Javascript Class, added to the displayed pages.
 * Catches iTunes-api calls from pages, such as http://r.mzstatic.com/htmlResources/6018/dt-storefront-base.jsz
 */
function player () {
	this.playURL = function(input) {
		var div = document.createElement("div");
		div.setAttribute("class","quick-view video movie active activity-video-dialog");
		div.setAttribute("style","width:50%; height:auto; position:fixed; left: 25%; float: top ; top:10px");
		div.setAttribute("id","previewer-container")
		a = document.createElement("a");
		a.setAttribute("class","close-preview");
		a.addEventListener("click",function() {
			this.parentNode.parentNode.removeChild(this.parentNode);
		} );
		div.appendChild(a);
		var vid = document.createElement("video");
		vid.id = "previewPlayer";
		vid.setAttribute("controls","true")
		div.appendChild(vid)
		document.body.appendChild(div);
		document.getElementById("previewPlayer").src=input.url;
		document.getElementById("previewPlayer").play()
		return "not 0";
	};
	this.stop = function() {
		document.getElementById("previewPlayer").pause();
		document.getElementById("previewer-container").parentNode.removeChild(document.getElementById("previewer-container"))
		return true;
	};
	this.doAnonymousDownload = function(obj) {
		alert(obj.url);
		//It has the url... just needs a way to tell the main program to download it.
	}
}

document.onload= new function() {
	iTunes = new player();
	
	//Fix <a target="external" etc.
	as = document.getElementsByTagName("a");
	for (a in as) {as[a].target=""};
}
