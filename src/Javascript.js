/*
 iTunes Javascript Class, added to the displayed pages.
 Catches iTunes-api calls from pages, such as
 http://r.mzstatic.com/htmlResources/6018/dt-storefront-base.jsz

 Copyright (C) 2009 - 2012 Luke Bryan
               2011 - 2012 Rogério Theodoro de Brito
               and other contributors.

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
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
	

	getPreferences: function() {
		"use strict";
		return {
			pingEnabled: true
		};
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
		if (xml.indexOf("<key>navbar</key>") === -1) {
			console.log("TunesViewer: adding download: " + xml);
			location.href = "download://" + xml;
		}
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


/*jslint unparam: true*/
function iTSVideoPreviewWithObject(a) {
	console.log("TunesViewer: In function <iTSVideoPreviewWithObject>");
    this.element = a;
    this.previewWidth = a.getAttributeWithDefault("video-preview-width", "700").toInt();
    this.previewHeight = a.getAttributeWithDefault("video-preview-height", "293").toInt()
}
iTSVideoPreviewWithObject.prototype = {
    play: function () {
    	console.log("TunesViewer: In function <iTSVideoPreviewWithObject#play>");
        var b = this.element.getAttribute("video-preview-url");
        var e = this.element.getAttributeWithDefault("preview-title", "");
        var f = this.element.getAttributeWithDefault("preview-artist", "");
        var a = this.element.getAttributeWithDefault("preview-album", "");
        var d = this.element.getAttributeWithDefault("preview-class", "");
        this.previewDuration = this.element.getAttributeWithDefault("preview-duration", "");
        // Creating a video HTML5 element, used in http://camendesign.com/code/video_for_everybody/test.html as example
        this.preview = document.createElement("video");
        //this.preview.setAttribute('controls', 'controls'); // TBD: bug showing controls
        this.preview.setAttribute('autoplay', 'autoplay');
        this.preview.setAttribute("width", this.previewWidth);
        this.preview.setAttribute("height", this.previewHeight);
        var previewSource = document.createElement("source");
        previewSource.setAttribute('src', b);
        previewSource.setAttribute('type', 'video/mp4');
        this.preview.appendChild(previewSource);
        if (this.element.getAttribute("hide-tooltip") != "true") {
            this.preview.setAttribute("title", e)
        }
        its.kit.sendToController("iTSShowcaseController", "pause");
        this.setContainer(d);
        this.container.style.width = "inherit";
        this.container.style.height = "auto";
        this.container.style.visibility = "hidden";
        var g = document.createElement("div");
        g.style.width = this.previewWidth + "px";
        g.style.height = this.previewHeight + "px";
        g.style.padding = '60px 0px 0px 0px';
        this.shade = document.createElement("div");
        this.shade.className = "shade";
        this.shade.style.background = "rgba(0,0,0,0)";
        this.shade.style.position = "fixed";
        this.shade.style.top = "0";
        this.shade.style.right = "0";
        this.shade.style.bottom = "0";
        this.shade.style.left = "0";
        document.body.appendChild(this.shade);
        this.shade.addEventListener("click", this, false);
        document.body.appendChild(this.container);
        this.container.appendChild(g);
        this.container.center("fixed");
        g.appendChild(this.preview);
        this.container.style.visibility = "";
        window.addEventListener("ended", this, false);
            
        var c = document.createEvent("Events");
        c.initEvent(iTSVideoPreview.Events.VIDEO_PLAYED, true, true);
        c._customEvent = true;
        c.adamId = this.element.getAttribute("adam-id");
        this.element.dispatchEvent(c)
    },
    playWithinQuickView: function () {
    	console.log("TunesViewer: In function <iTSVideoPreviewWithObject#playWithinQuickView>");
        this.container = this.element.parentByClassName("quick-view");
        var a = this.container.querySelector(".quick-view-wrapper");
        var i = a.querySelector(".movie-data, .episode-data, .music-video-data");
        var g = a.querySelectorAll("div.movie-trailer-title, div.pagination-controls");
        var c = a.clientWidth;
        var e = a.clientHeight;
        var f = c;
        var j = this.computeHeight(c, e);
        var k = 0;
        var l = 0;
        var b = this.element.parentByClassName("quick-view-wrapper");
        g.each(function (m) {
            l += m.offsetHeightPlusMargin()
        });
        b.querySelectorAll(".movie-data, .episode-data, .music-video-data").each(function (m) {
            k += m.offsetHeightPlusMargin()
        });
        if ((k != 0 || l != 0) && (j + l + 38 + k) > e) {
            var h = (e - k - l);
            if (l != 0) {
                h -= 38
            }
            if (this.computeWidth(h) < c) {
                f = this.computeWidth(h);
                j = this.computeHeight(f, h)
            }
        }
        this.preview.setAttribute("width", f);
        this.preview.setAttribute("height", j);
        this.element.insertAfter(this.preview);
        window.addEventListener("timeupdate", this, false);
        var d = b.offsetHeightPlusMargin() - k - j;
        this.preview.style.marginTop = d / 2 + "px";
        if (i) {
            i.style.width = c + "px"
        }
    },
    currentTime: function currentTime() {
    	console.log("TunesViewer: In function <iTSVideoPreviewWithObject#currentTime>");
        return iTunes.currentTime * 1000
    },
    handleEvent: function (a) {
    	console.log("TunesViewer: In function <iTSVideoPreviewWithObject#handleEvent>");
        if (a.type == "click") {
            this.stop()
        }
        if (a.type == "timeupdate") {
            var b = this.previewDuration - this.currentTime();
            if (b < 1000) {
                defer(this, "skipToNextPreview", b);
                window.removeEventListener("timeupdate", this, false)
            }
        }
    },
    skipToNextPreview: function () {
    	console.log("TunesViewer: In function <iTSVideoPreviewWithObject#skipToNextPreview>");
        var b = this.element.parentByClassName("quick-view-wrapper");
        if (!b) {
            return
        }
        var c = b.querySelector("div.pagination-controls > a.page-link.active");
        if (!c) {
            return
        }
        if (c.nextElementSibling != null) {
            var a = document.createEvent("MouseEvents");
            a.initMouseEvent("click", true, true, document.defaultView, 1, 0, 0, 0, 0, false, false, false, false, 0, null);
            c.nextElementSibling.dispatchEvent(a)
        }
    },
    stop: function () {
    	console.log("TunesViewer: In function <iTSVideoPreviewWithObject#stop>");
        if (this.container) {
            this.container.remove();
            this.shade.remove()
        }
        its.kit.sendToController("iTSShowcaseController", "resume");
        var a = document.createEvent("Events");
        a.initEvent("its:videopreview:stoped", true, true);
        a._customEvent = true;
        this.element.dispatchEvent(a)
    },
    setContainer: function (b) {
    	console.log("TunesViewer: In function <iTSVideoPreviewWithObject#setContainer>");
        var a = "quick-view video movie active";
        if (b) {
            a += " " + b
        }
        this.container = newElement("div", "", a);
        this.closeLink = this.getCloseLink();
        this.closeLink.addEventListener("click", this, false);
        this.container.appendChild(this.closeLink);
        if (its.client.screenReaderRunning()) {
            this.closeLink.focus()
        }
    },
    getCloseLink: function () {
    	console.log("TunesViewer: In function <iTSVideoPreviewWithObject#getCloseLink>");
        var a = newElement("a", "", "close-preview");
        a.setAttribute("role", "button");
        if (its.client.screenReaderRunning()) {
            a.tabIndex = 0
        }
        return a
    },
    computeHeight: function (b, a) {
    	console.log("TunesViewer: In function <iTSVideoPreviewWithObject#computeHeight>");
        if (this.previewWidth && this.previewHeight) {
            return Math.round((b * this.previewHeight) / this.previewWidth)
        }
    },
    computeWidth: function (a) {
    	console.log("TunesViewer: In function <iTSVideoPreviewWithObject#computeWidth>");
        if (this.previewWidth && this.previewHeight) {
            return Math.round((a * this.previewWidth) / this.previewHeight)
        }
    }
};
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


/* Hooking everything when the document is shown.
 *
 * FIXME: This huge thing has to be broken down into smaller pieces with
 * properly named functions.
 */
document.onpageshow = (function () {
	"use strict";
	var as, a, css, divs, i, j, rss, previews, buttons, clickEvent, downloadMouseDownEvent, subscribePodcastClickEvent, disabledButtonClickEvent;

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
