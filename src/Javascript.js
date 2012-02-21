/*
 * iTunes Javascript Class, added to the displayed pages.
 * Catches iTunes-api calls from pages, such as
 * http://r.mzstatic.com/htmlResources/6018/dt-storefront-base.jsz
 */

/*global window */

iTunes = { // All called from the page js:
	getMachineID: function () {
		"use strict";
		// FIXME: Apple's javscript tries to identify what machine we are
		// when we click on the "Subscribe Free" button of a given course to
		// create an URL.
		//
		// We should see what are some valid values and use those.
		console.log("TunesViewer: In function <getMachineID>");

		return "";
	},


	doDialogXML: function (b, d) {
		"use strict";
		/*
		// FIXME: This seems to be called for the creation of a
		// confirmation / license agreement dialog.
		//
		// Not yet sure how exactly this should work.
		var i;
		console.log("TunesViewer: In function <doDialogXML>, b:" + b);
		console.log("TunesViewer: In function <doDialogXML>, d:" + d);

		for (i in d) {
		console.log("TunesViewer: " + i + " " + d[i]);
		}

		return d.okButtonAction(); */
	},

	playURL: function (input) {
		"use strict";

		// Construct the preview display:
		var div, anchor, video;

		// First, create the div element
		div = document.createElement("div");
		div.setAttribute("class", "quick-view video movie active activity-video-dialog");
		div.setAttribute("style", "width:50%; height:auto; position:fixed; left: 25%; float: top ; top:10px");
		div.setAttribute("id", "previewer-container");

		// Create the anchor and tie it with the div element
		anchor = document.createElement("a");
		anchor.setAttribute("class", "close-preview");
		anchor.addEventListener("click", function () {
			this.parentNode.parentNode.removeChild(this.parentNode);
		}, false);
		div.appendChild(anchor);

		// Create a video element and tie it with the div element
		video = document.createElement("video");
		video.id = "previewPlayer";
		video.setAttribute("controls", "true");
		div.appendChild(video);
		document.body.appendChild(div);

		// Start the media:
		document.getElementById("previewPlayer").src = input.url;
		document.getElementById("previewPlayer").play();
		return "not 0";
	},

	showMediaPlayer: function (url_, showtype, title) {
		"use strict";
		playURL({url: url_});
	},

	openURL: function (url) {
		"use strict";
		location.href = url;
	},

	/** Download a file described as XML */
	addProtocol: function (xml) {
		"use strict";
		console.log("TunesViewer: adding download: " + xml);
		location.href = "download://" + xml;
	},

	/** Stops the preview player */
	stop: function () {
		"use strict";
		document.getElementById("previewer-container").parentNode.removeChild(document.getElementById("previewer-container"));
		return true;
	},

	doPodcastDownload: function (obj, number) {
		"use strict";
		alert("podcastdownload");
		//var keys = obj.getElementsByTagName('key');
	},

	doAnonymousDownload: function (obj) {
		"use strict";
		location.href = obj.url;
		// It has the url... just needs a way to tell the main
		// program to download it (webkit transaction?)
	},

	getUserDSID: function () { // no user id.
		"use strict";
		return 0;
	},

	putURLOnPasteboard: function (a, bool) {
		"use strict";
		location.href = "copyurl://" + encodeURI(a);
	},

	/** What version of webkit we're using, eg 'AppleWebKit/531.2' */
	webkitVersion: function () {
		"use strict";
		return (/AppleWebKit\/([\d.]+)/).exec(navigator.userAgent)[0];
	}

};


/*jslint unparam: false*/
function defined(something) {
	"use strict";
	console.log("TunesViewer: Entering the function <defined>.");
	return true;
}

/*jslint unparam: true*/
function iTSVideoPreviewWithObject(obj) {
	"use strict";
	console.log("TunesViewer: Entering the function <iTSVideoPreviewWithObject>.");
	// This was meant to figure out how to get non-working previews to play.
	// Unfortunately it gets called many times when you click 'i' on course icon,
	// freezing the application.
	//alert(obj);
}
/*jslint unparam: false*/

function fixTransparent(objects) {
	"use strict";
	var i;
	console.log("TunesViewer: Entering the function <fixTransparent>.");
	for (i = 0; i < objects.length; i++) {
		// If the heading is transparent, show it.
		if (window.getComputedStyle(objects[i]).color === "rgba(0, 0, 0, 0)") {
			objects[i].style.color = "inherit";
		}

		// Fix odd background box on iTunesU main page
		if (objects[i].parentNode.getAttribute("class") === "title") {
			objects[i].style.background = "transparent";
		}
	}
}

/**
 * Empty function to assign to events that we want to kill.
 */
function TunesViewerEmptyFunction() {
	"use strict";
}

/**
 * Function to remove event listeners (onmouseover, onclick, onmousedown)
 * of objects that we don't want to "have life".
 */
function removeListeners(objects) {
	"use strict";
	var i;
	console.log("TunesViewer: Entering the function <removeListeners>.");
	for (i = 0; i < objects.length; i++) {
		objects[i].onmouseover = TunesViewerEmptyFunction;
		objects[i].onclick = TunesViewerEmptyFunction;
		objects[i].onmousedown = TunesViewerEmptyFunction;
	}
}

/**
 * Function to create a player for preview of media.
 */
function previewClick (el) {
	"use strict";
	var tr, preview;

	console.log("TunesViewer: in previewClick.");

	tr = el.parentNode;
	preview = null;
	if (tr.hasAttribute('video-preview-url')) {
		preview = tr.getAttribute('video-preview-url');
	} else if (tr.hasAttribute('audio-preview-url')) {
		preview = tr.getAttribute('audio-preview-url');
	} else {
		console.log("TunesViewer: Unhandled case in previewClick.");
	}
	playURL({ url: preview });
}


/* Hooking everything when the document is shown.
 *
 * FIXME: This huge thing has to be broken down into smaller pieces with
 * properly named functions.
 */
document.onpageshow = (function () {
	"use strict";
	var as, a, css, divs, i, j, rss, previews, buttons, clickEvent, downloadMouseDownEvent, previewClick, subscribePodcastClickEvent, disabledButtonClickEvent;

	// Fix <a target="external" etc.

	// `as` is a list of anchors, `a` iterates over the list
	as = document.getElementsByTagName("a");
	for (a in as) {
		if (as.hasOwnProperty(a)) {
			if (as[a].target === "_blank") {
				as[a].target = "";
				as[a].href = "web" + as[a].href;
			} else if (as[a].target) {
				as[a].target = "";
			}
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

	// FIXME: Should we change this to be a separate function "attached"
	// to an object that is, finally, assigned to the onpageshow event?
	clickEvent = function (rss) {
		console.log("TunesViewer: click event listener: " + rss);
		location.href = rss;
	};

	// FIXME: Should we change this to be a separate function "attached"
	// to an object that is, finally, assigned to the onpageshow event?
	downloadMouseDownEvent = function (downloadUrl) {
		console.log('TunesViewer: opening: ' + downloadUrl);
		location.href = downloadUrl;
	};

	// fix free-download links, mobile
	for (i = 0; i < divs.length; i++) {
		if (divs[i].getAttribute("download-url") !== null &&
		    divs[i].textContent.indexOf("FREE") !== -1) {
			console.log("TunesViewer: getting attribute: " + divs[i].getAttribute("download-url"));
			removeListeners(divs[i].childNodes);
			divs[i].innerHTML = "<button onclick='window.event.stopPropagation();location.href=\"" + divs[i].getAttribute("download-url") + "\";'>Download</button>";
			divs[i].addEventListener('mouseDown', downloadMouseDownEvent(getAttribute('download-url')), false);
		}
		if (divs[i].getAttribute("role") === "button" &&
			divs[i].getAttribute("aria-label") === "Subscribe Free") {
			rss = "";
			console.log("TunesViewer: subscribe-button");
			removeListeners(divs[i].parentNode);
			removeListeners(divs[i].parentNode.parentNode);
			for (j = 0; j < divs.length; j++) {
				if (divs[j].getAttribute("podcast-feed-url") !== null) {
					rss = divs[j].getAttribute("podcast-feed-url");
					console.log("TunesViewer: RSS:" + rss);
				}
			}
			divs[i].addEventListener('click', clickEvent(rss), false);
		}
	}

	// FIXME: Should we change this to be a separate, named function
	// passed to the event?
	//
	// Fix non-working preview buttons:
	window.setTimeout(function() {
		previews = document.getElementsByClassName('podcast-episode');

		console.log("TunesViewer: number of previews: " + previews.length);
		for (i = 0; i < previews.length; i++) {
			console.log(previews[i].tagName);
			if (previews[i].tagName === 'TR') {
				console.log("TunesViewer: adding listener for preview: " + previews[i].tagName);
				console.log(previews[i].childNodes[1].childNodes[1].tagName);
				previews[i].childNodes[1].childNodes[1].id = "importantnode"; //check in inspector. doesn't work.
				previews[i].childNodes[1].childNodes[1].addEventListener('mousedown', previewClick, false);

			}
		}
	}, 3000);

	// FIXME: Should we change this to be a separate, named function
	// passed to the event?
	window.setTimeout(function () {
		var i;
		previews = document.getElementsByClassName('circular-preview-control');
		console.log("TunesViewer: number of previews: " + previews.length);
		for (i = 0; i < previews.length; i++) {
			previews[i].parentNode.parentNode.addEventListener('click', previewClick, false);
		}
	}, 10000);

	buttons = document.getElementsByTagName('button');

	// FIXME: Should we change this to be a separate function "attached"
	// to an object that is, finally, assigned to the onpageshow event?
	subscribePodcastClickEvent = function (subscribePodcastUrl) {
		location.href = subscribePodcastUrl;
	};

	// FIXME: Should we change this to be a separate function "attached"
	// to an object that is, finally, assigned to the onpageshow event?
	disabledButtonClickEvent = function (episodeUrl, artistName, itemName) {
		location.href = "download://<xml><key>URL</key><value><![CDATA[" + episodeUrl + "]]></value>" +
			"<key>artistName</key><value><![CDATA[" + artistName + "]]></value>" +
			"<key>fileExtension</key><value>zip</value>" +
			"<key>songName</key><value><![CDATA[" + itemName + "]]></value></xml>";
	};

	for (i = 0; i < buttons.length; i++) {
		if (buttons[i].innerHTML === "Subscribe Free" &&
		    buttons[i].getAttribute('subscribe-podcast-url') !== null) {
			buttons[i].addEventListener('click',
						    subscribePodcastClickEvent(buttons[i].getAttribute('subscribe-podcast-url')),
						    true);
		}
		if (buttons[i].hasAttribute("disabled")) {
			removeListeners(buttons[i]);
			buttons[i].addEventListener('click',
						    disabledButtonClickEvent(buttons[i].getAttribute("episode-url"),
									     buttons[i].getAttribute("artist-name"),
									     buttons[i].getAttribute('item-name')),
						    false);
			buttons[i].removeAttribute("disabled");
		}
	}

	//Fix 100% height
	if (document.getElementById('search-itunes-u') !== null) {
		document.getElementById('search-itunes-u').style.height = 90;
	}
	if (document.getElementById('search-podcast') !== null) {
		document.getElementById('search-podcast').style.height = 90;
	}

	// Fix selectable text, and search form height
	css = document.createElement("style");
	css.type = "text/css";
	css.innerHTML = "* { -webkit-user-select: initial !important } div.search-form {height: 90}";
	document.body.appendChild(css);
	console.log("TunesViewer: JS OnPageShow Ran Successfully.");

}()); // end Pageshow.
