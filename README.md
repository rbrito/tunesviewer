# TunesViewer

TunesViewer is a small, easy to use program to access iTunes-university
media and podcasts in Linux.

## Features:

* Direct searching, browsing, and downloading.
* Supports itunes-University login, to download students-and-staff-only
  media.
* Reveals the standard rss-podcast-feed of the itunes-podcasts, for use in
  any podcast software.
* Includes the option to set itself as default protocol handler, to go
  directly from the "loading itunes-U..." page to viewing with TunesViewer.

## Non-Features:

* Automatic podcast updates, auto-downloads and transfers: this program
  isn't a general-purpose podcast manager, but it can add podcasts to
  rhythmbox/gpodder/amarok/etc.
* iTunes Store: this will not let you connect to iTunes store accounts or
  buy anything.

## Minimum System Requirements:

Tunesviewer works well even on older computers, but you *must* have
`pygtk` >= 2.16 and `lxml` available. This shouldn't be a problem for
recent versions of Ubuntu, Fedora etc., as these prerequisites should be
taken care of automatically by package managers.

## Installation:

1.  Download the install package: ([.deb installer][0] for Ubuntu/Debian
    based operating systems, [.rpm installer][1] for Fedora/Red Hat based
    operating systems).

2.  Open the package and it should install. After installing, you should see
    TunesViewer on your Applications - Internet menu.

3.  Important post-installation setup: Go to TunesViewer preferences (in the
    Edit menu), and select the download-folder. Choose the folder you want
    to download to. If you select your rhythmbox/amarok library directory
    they should automatically add to your library.

The main [project of TunesViewer][2] is hosted on [SourceForge.net][3].

## Running from Git Checkout

After checking out the latest master (or other branch), double click and run src/Tunesviewer.py.

## Building a Debian Package

Building a Debian Package from the git repository, ready for installation in
your system is as easy as:

1. Installing the packages `build-essential`, `debhelper`, `fakeroot`, and `python`
2. Checking out the `debian` branch of this project (and optionally merging in other branch)
3. Typing `fakeroot debian/rules clean binary`

If you encounter problems, make sure debian/rules and the python files in src/ are executable.

## Experimental Debian Packages

Moderately recent and ready-to-install packages for Debian-based systems
(like Ubuntu, Linux mint and others) taken from this development tree are
provided in [Rogério Theodoro de Brito's PPA][4].

You are welcome to install them and to report potential issues with respect
to the packaging in this [project's issue tracker][5].


[0]: http://sourceforge.net/projects/tunesviewer/files/tunesviewer_1.5.2.deb/download
[1]: http://sourceforge.net/projects/tunesviewer/files/tunesviewer-1.4.noarch.rpm/download
[2]: http://sourceforge.net/projects/tunesviewer
[3]: http://sourceforge.net
[4]: https://launchpad.net/~rbrito/+archive/ppa/
[5]: https://github.com/rbrito/tunesviewer/issues
