/*
 * iTunes Javascript Class, added to the displayed pages.
 * Catches iTunes-api calls from pages, such as
 * http://r.mzstatic.com/htmlResources/6018/dt-storefront-base.jsz
 */
function player() {
	this.playURL = function (input) {
		// Construct the preview display:
		var div = document.createElement("div");
		div.setAttribute("class", "quick-view video movie active activity-video-dialog");
		div.setAttribute("style", "width:50%; height:auto; position:fixed; left: 25%; float: top ; top:10px");
		div.setAttribute("id", "previewer-container");
		a = document.createElement("a");
		a.setAttribute("class", "close-preview");
		a.addEventListener("click", function () {
			this.parentNode.parentNode.removeChild(this.parentNode);
		});
		div.appendChild(a);
		var vid = document.createElement("video");
		vid.id = "previewPlayer";
		vid.setAttribute("controls", "true");
		div.appendChild(vid);
		document.body.appendChild(div);
		// Start the media:
		document.getElementById("previewPlayer").src = input.url;
		document.getElementById("previewPlayer").play();
		return "not 0";
	};
	
	this.showMediaPlayer = function(url,showtype,title) {
		obj = function () {};
		obj.url = url;
		this.playURL(obj);
	};
	
	this.openURL = function(url) {
		location.href = url;
	};
	
	this.addProtocol = function (xml) {
		console.log(xml);
		location.href="download://"+xml
		/*xml = new DOMParser().parseFromString(xml, "text/xml");
		keys = xml.getElementsByTagName('key');
		for (var i=0; i<keys.length; i++) {
			if (keys[i].textContent=="URL") {//Goto the download url.
				document.location = keys[i].nextSibling.textContent;
			}
		}*/
	};

	this.stop = function () {
		//document.getElementById("previewPlayer").pause();
		document.getElementById("previewer-container").parentNode.removeChild(document.getElementById("previewer-container"));
		return true;
	};

	this.doPodcastDownload = function (obj, number) {
		alert("podcastdownload");
		keys = obj.getElementsByTagName('key');
	};

	this.doAnonymousDownload = function (obj) {
		location.href = obj.url;
		// It has the url... just needs a way to tell the main
		// program to download it (webkit transaction?)
	};

	this.getUserDSID = function () {//no user id.
		return 0;
	};
}

function defined(something) {
	return true;
}

function iTSVideoPreviewWithObject(obj) {
	// This was meant to figure out how to get non-working previews to play.
	// Unfortunately it gets called many times when you click 'i' on course icon,
	// freezing the application.
	//alert(obj);
}

function fixTransparent(objects) {
	for (i = 0; i < objects.length; i++) {
		// If the heading is transparent, show it.
		if (window.getComputedStyle(objects[i]).color == "rgba(0, 0, 0, 0)") {
			objects[i].style.color = "inherit";
		}

		// Fix odd background box on iTunesU main page
		if (objects[i].parentNode.getAttribute("class") == "title") {
			objects[i].style.background = "transparent";
		}
	}
}


document.onpageshow = new function () {
	iTunes = new player();
	its.webkitVersion = function webkitVersion() {
		return "AppleWebKit/531.1";
	};

	// Fix <a target="external" etc.
	as = document.getElementsByTagName("a");
	for (a in as) {
		if (as[a].target == "_blank") {
			as[a].target = "";
			as[a].href = "web" + as[a].href;
		} else if (as[a].target) {
			as[a].target = "";
		}
	}

	/* This fixes the color=transparent style on some headings.
	 * Unfortunately, you can't use document.styleSheets' CSSRules/rules
	 * property, since it's cross-domain:
	 *
	 * http://stackoverflow.com/questions/5678040/cssrules-rules-are-null-in-chrome
	 *
	 * So, it manually checks for elements with the style:
	 */
	fixTransparent(document.getElementsByTagName("h1"));
	fixTransparent(document.getElementsByTagName("h2"));
	fixTransparent(document.getElementsByTagName("div"));
	fixTransparent(as);
	
	divs = document.getElementsByTagName("div");
	for (var i=0; i<divs.length; i++) { // fix free-download links, mobile
		if (divs[i].getAttribute("download-url") != null && divs[i].textContent.indexOf("FREE")!=-1) {
			console.log(divs[i].getAttribute("download-url"));
			removeListeners(divs[i].childNodes);
			divs[i].innerHTML = "<button onclick='window.event.stopPropagation();location.href=\""+divs[i].getAttribute("download-url")+"\";'>Download</button>";
			divs[i].addEventListener('mouseDown',function () {console.log('opening'+this.getAttribute('download-url'));
			                                              location.href = this.getAttribute('download-url'); })
		}
		if (divs[i].getAttribute("role")=="button" && divs[i].getAttribute("aria-label")=="SUBSCRIBE FREE") {
			rss = "";
			console.log("subscribe-button");
			removeListeners(divs[i].parentNode);
			removeListeners(divs[i].parentNode.parentNode);
			for (var j=0; j<divs.length; j++) {
				if (divs[j].getAttribute("podcast-feed-url") != null) {
					rss = divs[j].getAttribute("podcast-feed-url");
					console.log("rss:"+rss);
				}
			}
			divs[i].addEventListener('click', function () {console.log(rss);location.href = rss});
		}
	}

	// Mouse-over tooltip for ellipsized title...
	// Unfortunately it seems this may cause X window error!
	/*titles = document.getElementsByClassName('name')
	for (i=0; i<titles.length; i++) {
		titles[i].title = titles[i].textContent
	}
	titles = document.getElementsByClassName('artist')
	for (i=0; i<titles.length; i++) {
		titles[i].title = titles[i].textContent
	}*/

	// Fix non-working preview buttons:
	previews = document.getElementsByClassName('podcast-episode');
	console.log(previews.length);
	for (i = 0; i < previews.length; i++) {
		if (previews[i].tagName == 'tr') {
			console.log(previews[i].tagName);
			previews[i].childNodes[0].addEventListener('click', previewClick);
		}
	}
	window.setTimeout(function () {
		previews = document.getElementsByClassName('circular-preview-control');
		console.log('previews' + previews.length);
		for (i = 0; i < previews.length; i++) {
			previews[i].parentNode.parentNode.addEventListener('click', previewClick);
		}
	}, 10000);

	buttons = document.getElementsByTagName('button');
	for (i = 0; i < buttons.length; i++) {
		if (buttons[i].getAttribute('subscribe-podcast-url') != null) {
			buttons[i].addEventListener('click', function () { location.href = this.getAttribute('subscribe-podcast-url'); }, true);
		}
	}

        //Fix 100% height
	if (document.getElementById('search-itunes-u') != null) {
		document.getElementById('search-itunes-u').style.height = 90;
	}
	if (document.getElementById('search-podcast') != null) {
		document.getElementById('search-podcast').style.height = 90;
	}
	console.log("JS OnPageShow Ran Successfully.");
};

function removeListeners(objects) {
	for (var i=0; i<objects.length; i++) {
		objects[i].onmouseover = (function () {});
		objects[i].onclick = (function () {});
		objects[i].onmousedown = (function () {});
	}
}

function previewClick(el) {
	console.log('previewclick');
	tr = el.parentNodel;
	if (tr.hasAttribute('video-preview-url')) {
		preview = tr.getAttribute('video-preview-url');
	} else if (tr.hasAttribute('audio-preview-url')) {
		preview = tr.getAttribute('audio-preview-url');
	}
	a = new function () { this.url = preview; }
	new player().playURL(a);
};
