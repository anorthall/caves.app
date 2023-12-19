# Changes to caves.app
A summary of changes made to caves.app, organised by version, can be found below.

## Version 2.0.1
Version 2.0.1 of caves.app was released on Tuesday, 19th December 2023.

### Changes
#### User profiles
- The trip list has been redesigned to allow easier viewing and management of trips.
- Column sorting has been improved and a bug with distance field sorting fixed.
- Users who disable distance or survey statistics will now see location related fields
in their trip list instead.
- Clicking a trip now opens a modal with details of the trip, removing the need to visit
the trip page to review details.
- An advanced search feature, accessed by clicking the caret on the right of the quick search
bar, has been added. Trips can be filtered and searched by specific fields.
- The ability to hide statistics from your profile has been removed. This feature originally existed
for aesthetic reasons, and since statistics are now in their own tab, the ability to hide them is no
longer required. Statistics will only be shown to people who can view your profile, in accordance with
your privacy settings.
- A profile view counter has been added, accessible via the quick stats in the right hand sidebar, or
via the info tab. Users can only view their own profile view count.
- A bug where no 'Add friend' link was shown on smaller screens has been fixed.
- A bug preventing the photos tab being shown when the user had less than 40 photos has been fixed.
- The ability to show a list of cavers under each trip on the trip list has been removed.

#### Trip detail page
- A trip view counter has been added. Users can only view the view count for their own trips. The
view count will increment if trips are viewed in the trip feed, or by accessing the trip page. Trips
viewed via a modal from the user profile page do not increment the view count.
- The featured photo cropping tool will now show a loading spinner until such time the image to crop
has loaded.

#### Trip photos page
- The uploader will now redirect you to the trip detail page when all uploads have finished successfully.

#### Trip feed page
- A bug preventing photos showing on some trips has been fixed.

#### Cave map page
- A bug where some locations were not accepted for geocoding has been fixed.

#### Staff dashboard
- Additional statistics on recent user activity, anonymised for privacy purposes, have been added.

#### Account page
- A bug where the account page stated the profile was private, when it was not, has been fixed.

## Version 2.0.0
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
- The 'trip report' field has been renamed to 'public notes'. The 'notes' field has been renamed
to 'private notes'. Private notes are always private, public notes are always visible to anyone who
can view the trip.

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
- The 'trip report' field has been renamed to 'public notes'. The 'notes' field has been renamed
to 'private notes'. Private notes are always private, public notes are always visible to anyone who
can view the trip.

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
- Public notes (formerly trip reports) now *only* support Markdown - the previous rich
text editor is no longer used.
- Images are no longer allowed in public notes.
- Several bugs were fixed that related to viewing trips when not logged in.

#### Trip photos page
- The featured photo can be deselected.
- The uploader has been restyled.

#### Trip feed page
- The trip feed has been redesigned to be inkeeping with the new design of the trip detail page.
- A featured photo, if selected, will be used as a header background for each trip.
- Public notes are now shown on the trip feed page, truncated depending on screen size.
- Several bugs were fixed that related to viewing trips when not logged in.

#### Trip add/edit page
- The rich text editor for public notes (formerly trip reports) has been replaced with a plain text area.
- A help link for Markdown has been added under the public notes field.
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
