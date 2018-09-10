# PanicSelect
This is a repository for a website that recommends a champion to pick during the champion selection phase in League of Legends.
The website considers the position that the user is playing, historical performance of the user with all applicable champions, performance of champions in the latest patch, and performance of champions against the champion that their lane opponent has picked (if applicable). 
Each champion is given a rating and a recommendation is made to the user.
The website also recommends runes, masteries and item builds for each champion that can be played.
All data is curated from the champion.gg and Riot APIs.

Front-end written with AngularJS and back-end written in Python with the help of the Flask framework.
