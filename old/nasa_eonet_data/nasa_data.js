
// Define US bounds
var minLat = 24.396308;
var maxLat = 49.384358;
var minLon = -125.0;
var maxLon = -66.93457;

//days
var days = 3650;

$(document).ready(function() {
    $.getJSON("https://eonet.gsfc.nasa.gov/api/v3/events/", {days: days,
                                                            bbox:  minLon + ',' + maxLat + ',' + maxLon + ',' + minLat,
                                                            status: 'all'
                                                        })
    .done(function(data) {
        var eventsList = data.events.map(function(event) {
            // Skip if the first category is 'manmade' and no second category
            if (event.categories[0].id === 'manmade' && event.categories.length < 2) {
                return null;
            }

            // Else determine what the category is
            var category = event.categories[0].id !== 'manmade' ? event.categories[0].id : event.categories[1].id;
            
            // Get other stats from the event
            var id = event.id ? event.id : null;
            var title = event.title ? event.title : null;

            // Skip if nothing in the geometry (datetime + coordinates)
            if (event.geometry.length === 0) {
                return null;
            }

            // Get the date and coordinates of the event
            var date = event.geometry[0].date ? event.geometry[0].date : null;
            var coords = event.geometry[0].coordinates ? event.geometry[0].coordinates : null;

            // Get the source of the event from the list
            var source = (event.sources && event.sources.length > 0) ? event.sources[0].id : null;


            // Return the event
            return {
                id: id,
                category: category,
                title: title,
                date: date,
                coords: coords,
                source: source
            };
        }).filter(function(event) { return event !== null; });  // Filter out null values

        
        // Log the number of events before and after filtering
        console.log("Number of events: " + data.events.length);
        console.log("Number of filtered events: " + eventsList.length);

        // Turns out all the filtering was useless since no difference in number of events
        // Whoops

        var filtered = {
            "title": "EONET US",
            "description": "EONET Events that occurred in the US.",
            "link": "https://eonet.gsfc.nasa.gov/api/v3/events",
            "events": eventsList };

        var jString = JSON.stringify(filtered, null, 4);
        $('#filteredData').text(jString);

        // Log the file to console
        console.log(jString);

    });
});