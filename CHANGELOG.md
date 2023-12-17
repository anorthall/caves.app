# Changes to caves.app
A summary of changes made to caves.app, organised by version, can be found below.

## Version 2.0
Version 2.0 of caves.app is the result of around a month of my free time and
consists of a complete stylistic and functional redesign of the application as
well as many new features and improvements to the user experience.

Version 2.0 was released on Sunday, 17th December, 2023.

### Highlights
- A complete redesign of the site.
- Dark mode has been added and is the default mode.
- A new photo gallery on user profile pages and trip detail pages.
- Improved user profile pages, with more information, laid out more sensibly.
- A new navbar and three column layout, and new notifications panel and dropdown menu.
- A new quick stats feature on user profiles.
- Numerous bugfixes and optimisations to backend code.

### All changes
#### General changes
- The site now uses a new three column layout.
- For smaller screens, a new dropdown menu is used.
- Users can select between light and dark mode.
- The navbar has been redesigned with icons instead of links.
- The notifications panel has been redesigned.
- A changes page has been added.
- All page headers have been standardised.
- All duration displays have been standardised to a *24h 0m* format.
- The search page has been temporarily removed until it can be improved.
- Most long form text on caves.app now uses a sensible line length for ease of reading.

#### User profiles
- A new header section shows the user and their avatar more prominently.
- Some basic stats are displayed in the header.
- The page shown if a user has a private profile has been redesigned.
- The option to select a profile page title has been removed. All profile pages will now
use the user's name as the title.
- All user information is now contained within tabs under the user biography.
- The trip list has been redesigned and made easier to use and read.
- The statistics table has been redesigned and a legend modal has been added.
- A **Photos** section has been added, with a gallery of all photos that a user has added.
- Users can hover over any photo to get a link to the trip the photo is attached to.
- An **Info** section has been added, with additional profile information and social media links.
- A **Quick stats** section will be shown in the righthand sidebar.
- A **Friends** section will show a longform friends list, with quick links shown in the right
sidebar.
- All of the above respect user privacy settings and will adapt based on who is viewing the profile.

#### Trip detail page
- A new justified photo gallery is now shown.
- Users can select a featured photo for each trip which will be displayed in the header.
- The header section has been redesigned to be more readable.
- Trip reports now *only* support Markdown - the previous rich text editor is no longer used.
- Images are no longer allowed in trip reports.
- Several bugs were fixed that related to viewing trips when not logged in.

#### Trip photos page
- The featured photo can be deselected.
- The uploader has been restyled.

#### Trip feed page
- The trip feed has been redesigned to be inkeeping with the new design of the trip detail page.
- A featured photo, if selected, will be used as a header background for each trip.
- Trip reports are now shown on the trip detail page, truncated depending on screen size.
- Several bugs were fixed that related to viewing trips when not logged in.

#### Trip add/edit page
- The rich text editor for trip reports has been replaced with a plain text area.
- A help link for Markdown has been added under the trip report field.
- The caver select field has been restyled to allow for dark mode.

#### Cave map page
- The cave map page now uses a dark theme.

#### Mobile dropdown menu
- The mobile dropdown menu has been redesigned.
- The mobile dropdown menu will show any links that were in the right hand sidebar if the right
hand sidebar becomes hidden due to screen size.

#### Notifications
- Notifications are now dynamic and grouped by trip.
- Notifications will update if more actions are taken - e.g. another user likes the trip.
- Fixed a bug where notifications became 'new' again when the user clicked them.

#### Statistics
- Numerous backend optimisations were made to the statistics code, mostly involving using
PostgreSQL to calculate statistics data, rather than Python code.

#### Registration
- A honey pot field has been added to prevent spam.

#### Home page for unregistered users
- Screenshots have been updated.
- Minor style changes.
- Feature fields updated.

#### Technical changes
- All versions of all dependencies have been updated.
- Uppy has been updated.
