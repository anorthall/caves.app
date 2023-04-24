# Social TODO

## Features
- [ ] Allow users to delete comments on objects they created
- [ ] Add full display of users that liked a trip
- [ ] Change export function to use django-import-export
- [ ] Add email preferences model
- [ ] Add email notifications of friend requests
- [ ] Add all tests listed below
- [X] Fix Distance field sorting bug
- [X] Fix liked trips queries (too many!)
- [X] Add option to disable email and/or username being used to add you as a friend
- [X] Add option to disable comments
- [X] Add trip likes
- [X] Add timeline feature to homepage
- [X] Add clubs and expeditions to the trip detail view
- [X] Add trip comments
- [X] Remove 'Public' module and integrate all Trip/Report/Trip List displays into one view
- [X] Change Trip and Trip Report delete links into a Bootstrap modal
- [X] Add sidebar to Account pages
- [X] Enable links to profiles from the friends page
- [X] Combine sidebar_trips.html and sidebar_trips_owner.html into one template
- [X] Create can_user_view function which determines if a user can view a specific object (Trip, TripReport)
- [X] Ensure user profile and settings are created at user creation
- [X] Abstract user profile to a separate model
- [X] Abstract user settings to a separate model
- [X] Change all references of user profile/settings to the relevant models

## Tests
- [ ] Test that all pages load with an appropriate status code

### Users
- [ ] Test that users can login
- [ ] Test that users can register
    - [ ] Test that emails are sent
    - [ ] Test that the correct verification code is accepted
    - [ ] Test that an incorrect verification code is rejected
    - [ ] Test that the user is logged in after verification
- [ ] Test that the resend verification email form works
- [ ] Test that the change email form works
    - [ ] Test that emails are sent
    - [ ] Test that the correct verification code is accepted
    - [ ] Test that an incorrect verification code is rejected
- [ ] Test that the change password form works
- [ ] Test that the password reset form works
- [ ] Test that the profile update form works
- [ ] Test that timezone settings work
- [ ] Test that distance settings work

#### Notifications
- [ ] Test the CavingUser.notify() method
- [ ] Test that notifications are displayed
- [ ] Test that the notification redirect page works

#### Friends
- [ ] Test that users can add friends
- [ ] Test that users can remove friends
- [ ] Test that users cannot add themselves as a friend
- [ ] Test that users cannot add friends which they are already friends with
- [ ] Test that all appropriate modals are generated with the correct links


### Logger
#### Trips
- [ ] Test the user profile/trip list page
      - [ ] Test that the sidebar does not appear
      - [ ] Test that privacy settings for the profile and individual trips are respected
      - [ ] Test that the trip list is sorted correctly
      - [ ] Test that the trip list is paginated correctly

- [ ] Test the trips sidebar
    - [ ] Test that edit and delete links for Trips only appear for the 'owner'
    - [ ] Test that the edit, create and delete links for TripReports only appear for the 'owner'
    - [ ] Test that view TripReport links appear for the owner
    - [ ] Test that view TripReport links appear for other users based on privacy
    - [ ] Test that view profile links appear for the owner
    - [ ] Test that view profile links appear for other users based on privacy
    - [ ] Test that all modals for delete links are generated correctly

- [ ] Test that a user can view their own trips
    - [ ] Test that the sidebar appears
    - [ ] Test that notes always appear regardless of private_notes setting

- [ ] Test that a user can view other user's trips
    - [ ] Test that the sidebar appears
    - [ ] Test all privacy settings: private, friends, public, default
    - [ ] Test that private_notes setting works

- [ ] Test the trip create form
    - [ ] Test that the sidebar appears
    - [ ] Test that the trip is saved to the correct user
    - [ ] Test that the trip saves and is viewable

- [ ] Test the trip update form
    - [ ] Test that the sidebar appears
    - [ ] Test that a user cannot update another user's trip
    - [ ] Test that the updates save

- [ ] Test the trip delete view
    - [ ] Test that a user cannot delete another user's trip
    - [ ] Test that the trip is deleted

#### Trip Reports
- [ ] Test that a user can view their own trip reports
    - [ ] Test that the sidebar appears
    - [ ] Test that trip report create/edit/delete links appear as applicable

- [ ] Test that a user can view other user's trip reports
    - [ ] Test that the sidebar appears
    - [ ] Test all privacy settings: private, friends, public, default

- [ ] Test the trip report create form
    - [ ] Test that a user cannot add a trip report for another user's trip
    - [ ] Test that the report links appear on the sidebar after creation

- [ ] Test the trip report update form
    - [ ] Test that a user cannot update another user's report
    - [ ] Test that the updates save

- [ ] Test the trip report delete view
    - [ ] Test that a user cannot delete another user's report
    - [ ] Test that the report is deleted

#### Other
- [ ] Test user template tag
- [ ] Test the import/export page (not yet implemented fully)
- [ ] Test the statistics page (needs a re-code - better to write tests after?)
- [ ] Test the statistics charts views


### Core
- [ ] Test News
- [ ] Test FAQs
