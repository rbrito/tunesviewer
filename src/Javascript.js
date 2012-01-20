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
	
	this.addProtocol = function (xml) {
		console.log(xml);
		xml = new DOMParser().parseFromString(xml, "text/xml");
		keys = xml.getElementsByTagName('key');
		for (var i=0; i<keys.length; i++) {
			if (keys[i].textContent=="URL") {//Goto the download url.
				document.location = keys[i].nextSibling.textContent;
			}
		}
	};

	this.stop = function () {
		//document.getElementById("previewPlayer").pause();
		document.getElementById("previewer-container").parentNode.removeChild(document.getElementById("previewer-container"));
		return true;
	};

	this.doPodcastDownload = function (obj, number) {
		alert("podcastdownload");
		//alert(obj.innerHTML)//getAttribute("episode-url"))
		keys = obj.getElementsByTagName('key');
		//alert(keys)
		/*name = ''; url='';
		for (i=0; i<keys.length; i++) {
			if (keys[i].textContent=="longDescription") {
				name = keys[i].nextSibling.textContent;
			} else if (keys[i].textContent = "episodeUrl") {
				url = keys[i].nextSibling.textContent;
			}
		}
		alert(name+"\n"+url);*/
	};

	this.doAnonymousDownload = function (obj) {
		//alert(obj.itemName + "\n"+obj.url);
		//location.href="download://"+encodeURI(obj.itemName)+" "+encodeURI(obj.url);
		location.href = obj.url;
		//It has the url... just needs a way to tell the main program to download it (webkit transaction?)
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

		//Fix odd background box on iTunesU main page
		if (objects[i].parentNode.getAttribute("class") == "title") {
			objects[i].style.background = "transparent";
		}
		/*if (window.getComputedStyle(headings[i]).backgroundImage
			.indexOf("-webkit-gradient(linear,") > -1) {
			headings[i].style.background = "transparent";
		}*/
	}
}


document.onpageshow = new function () {
	iTunes = new player();
	its.webkitVersion = function webkitVersion() {
		return "AppleWebKit/531.1";
	};

	//Fix <a target="external" etc.
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
	 * Unfortunately, you can't use document.styleSheets' CSSRules/rules property, since it's cross-domain:
	 * http://stackoverflow.com/questions/5678040/cssrules-rules-are-null-in-chrome
	 * So, it manually checks for elements with the style:
	 */
	fixTransparent(document.getElementsByTagName("h1"));
	fixTransparent(document.getElementsByTagName("h2"));
	fixTransparent(document.getElementsByTagName("div"));
	fixTransparent(as);

	//Mouse-over tooltip for ellipsized title...
	//Unfortunately it seems this may cause X window error!
	/*titles = document.getElementsByClassName('name')
	for (i=0; i<titles.length; i++) {
		titles[i].title = titles[i].textContent
	}
	titles = document.getElementsByClassName('artist')
	for (i=0; i<titles.length; i++) {
		titles[i].title = titles[i].textContent
	}*/

	//Fix non-working preview buttons:
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
			//if (previews[i].tagName=='div') {

			previews[i].parentNode.parentNode.addEventListener('click', previewClick);
			//}
		}
	}, 10000);

	buttons = document.getElementsByTagName('button');
	for (i = 0; i < buttons.length; i++) {
		if (buttons[i].getAttribute('subscribe-podcast-url') != null) {
			buttons[i].addEventListener('click', function () { location.href = this.getAttribute('subscribe-podcast-url'); }, true);
		}
		/*if (buttons[i].getAttribute('episode-url')!=null) {
			buttons[i].addEventListener('click',function () {alert(this.getAttribute('episode-url'))},true);
		}*/
	}
	if (document.getElementById('search-itunes-u') != null) {
		//Fix 100% height
		document.getElementById('search-itunes-u').style.height = 90;
	}
	if (document.getElementById('search-podcast') != null) {
		//Fix 100% height
		document.getElementById('search-podcast').style.height = 90;
	}
	console.log("JS OnPageShow Ran Successfully.");
};

function previewClick(el) {
	console.log('previewclick');
	tr = el.parentNodel;
	if (tr.hasAttribute('video-preview-url')) {
		preview = tr.getAttribute('video-preview-url');
	} else if (tr.hasAttribute('audio-preview-url')) {
		preview = tr.getAttribute('audio-preview-url');
	}
	a = new function () { this.url = preview; }//this.url="http://deimos3.apple.com/WebObjects/Core.woa/DownloadTrackPreview/matcmadison.edu-dz.5408889333.05408889335.5408889393/enclosure.mp4"}
	new player().playURL(a);
};
