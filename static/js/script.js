let map, userMarker, directionsService, directionsRenderer, autocomplete;
let currentLocation = null;
let clinicMarkers = [];

function initMap() {
    console.log("initMap called");
    if (!window.google || !google.maps || !google.maps.places) {
        console.error("Google Maps API not loaded properly");
        updateStatus("Failed to load maps service. Please refresh.", "error");
        return;
    }

    const defaultLocation = { lat: 22.5744, lng: 88.3629 }; // Centered on Kolkata

    // Create the map instance
    map = new google.maps.Map(document.getElementById("map"), {
        center: defaultLocation,
        zoom: 5 // Default zoom level
    });

    // Initialize Directions Service and Renderer
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({
        suppressMarkers: true,
        polylineOptions: { strokeColor: "#4e73df", strokeWeight: 4 }
    });
    directionsRenderer.setMap(map);

    // Setup Autocomplete for location search input
    const input = document.getElementById("location-search");
    if (input) {
        autocomplete = new google.maps.places.Autocomplete(input);
        autocomplete.addListener("place_changed", handlePlaceSelect);
    }

    // Attach event listener for the "Detect My Location" button
    document.getElementById("detect-location")?.addEventListener("click", detectLocation);

    // Initial status update
    updateStatus("Ready to search.");
}

function handlePlaceSelect() {
    const place = autocomplete.getPlace();

    if (!place.geometry) {
        updateStatus("Location not recognized. Please select from the suggestions.", "error");
        return;
    }

    const location = place.geometry.location.toJSON();
    currentLocation = location;

    map.setCenter(location);
    map.setZoom(15);
    placeUserMarker(location);
    findNearbyVets(location);
}

function detectLocation() {
    if (!navigator.geolocation) {
        updateStatus("Geolocation not supported by your browser.", "error");
        return;
    }

    updateStatus("Detecting location...");

    navigator.geolocation.getCurrentPosition(
        ({ coords }) => {
            const location = { lat: coords.latitude, lng: coords.longitude };
            currentLocation = location;

            map.setCenter(location);
            map.setZoom(15);
            placeUserMarker(location);
            findNearbyVets(location);

            const geocoder = new google.maps.Geocoder();
            geocoder.geocode({ location }, (results, status) => {
                if (status === "OK" && results[0]) {
                    document.getElementById("location-search").value = results[0].formatted_address;
                    updateStatus(`Detected: ${results[0].formatted_address}`);
                } else {
                    updateStatus("Location detected, but address could not be found.", "warning");
                }
            });
        },
        (error) => {
            const messages = {
                1: "Permission denied. Please enable location access in your browser settings.",
                2: "Location unavailable. Your device could not determine your position.",
                3: "Request timed out. Please try again."
            };
            updateStatus(messages[error.code] || "An unknown error occurred during geolocation.", "error");
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
}

function placeUserMarker(location) {
    if (userMarker) userMarker.setMap(null);

    userMarker = new google.maps.Marker({
        position: location,
        map: map,
        icon: "http://maps.google.com/mapfiles/ms/icons/blue-dot.png",
        title: "Your Location"
    });
}

function findNearbyVets(location) {
    updateStatus("Searching for clinics...");
    clearClinics();

    try {
        const service = new google.maps.places.PlacesService(map);
        
        service.nearbySearch({
            location: location,
            radius: 50000,
            type: "veterinary_care"
        }, (results, status) => {
            if (status === google.maps.places.PlacesServiceStatus.OK) {
                if (results && results.length) {
                    // Get detailed place information for each result
                    const detailedRequests = results.slice(0, 10).map(clinic => {
                        return new Promise((resolve) => {
                            service.getDetails({ placeId: clinic.place_id }, (place, status) => {
                                if (status === google.maps.places.PlacesServiceStatus.OK) {
                                    const distance = calculateDistance(
                                        location.lat, location.lng,
                                        place.geometry.location.lat(), place.geometry.location.lng()
                                    );
                                    resolve({
                                        ...place,
                                        distance
                                    });
                                } else {
                                    // If details fail, use basic info
                                    const distance = calculateDistance(
                                        location.lat, location.lng,
                                        clinic.geometry.location.lat(), clinic.geometry.location.lng()
                                    );
                                    resolve({
                                        ...clinic,
                                        distance
                                    });
                                }
                            });
                        });
                    });

                    Promise.all(detailedRequests).then(clinicsWithDetails => {
                        // Sort by distance (ascending)
                        clinicsWithDetails.sort((a, b) => a.distance - b.distance);
                        updateStatus(`Found ${clinicsWithDetails.length} clinics.`);
                        renderClinics(clinicsWithDetails);
                    });
                } else {
                    updateStatus("No clinics found in this area.", "info");
                }
            } else {
                console.error("Places API Error:", status);
                updateStatus("Error searching for clinics. Status: " + status, "error");
            }
        });
    } catch (error) {
        console.error("Places Service Error:", error);
        updateStatus("Failed to initialize Places service", "error");
    }
}

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Radius of the earth in km
    const dLat = deg2rad(lat2 - lat1);
    const dLon = deg2rad(lon2 - lon1); 
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
    return R * c; // Distance in km
}

function deg2rad(deg) {
    return deg * (Math.PI/180);
}

function renderClinics(clinics) {
    const list = document.getElementById("clinics-list");
    list.innerHTML = "";
    clinicMarkers = [];

    clinics.forEach((clinic, index) => {
        const phone = clinic.formatted_phone_number || "Phone not available";
        const address = clinic.vicinity || clinic.formatted_address || "Address not available";
        const website = clinic.website ? `<a href="${clinic.website}" target="_blank">Website</a>` : "";
        
        const item = document.createElement("div");
        item.className = "clinic-item";
        item.innerHTML = `
            <div class="clinic-header">
                <strong>${index + 1}. ${clinic.name}</strong>
                <span class="distance-badge">${clinic.distance.toFixed(1)} km</span>
            </div>
            <div class="clinic-details">
                <div><i class="fas fa-map-marker-alt"></i> ${address}</div>
                <div><i class="fas fa-phone"></i> ${phone}</div>
                ${clinic.rating ? `<div><i class="fas fa-star"></i> ${clinic.rating} (${clinic.user_ratings_total || 0} reviews)</div>` : ""}
                ${website ? `<div><i class="fas fa-globe"></i> ${website}</div>` : ""}
            </div>
            <button class="btn" onclick="getDirectionsTo('${clinic.place_id}')">
                <i class="fas fa-directions"></i> Get Directions
            </button>
        `;
        list.appendChild(item);

        const marker = new google.maps.Marker({
            position: clinic.geometry.location,
            map: map,
            title: clinic.name,
            icon: "http://maps.google.com/mapfiles/ms/icons/green-dot.png"
        });

        clinicMarkers.push(marker);

        const infoWindow = new google.maps.InfoWindow({
            content: `
                <div class="info-window">
                    <strong>${clinic.name}</strong><br>
                    <div><i class="fas fa-map-marker-alt"></i> ${address}</div>
                    <div><i class="fas fa-phone"></i> ${phone}</div>
                    <div><i class="fas fa-ruler"></i> ${clinic.distance.toFixed(1)} km away</div>
                    ${clinic.rating ? `<div><i class="fas fa-star"></i> ${clinic.rating} (${clinic.user_ratings_total || 0} reviews)</div>` : ''}
                    ${website ? `<div><i class="fas fa-globe"></i> ${website}</div>` : ''}
                    <button onclick="getDirectionsTo('${clinic.place_id}')">
                        <i class="fas fa-directions"></i> Directions
                    </button>
                </div>
            `
        });

        marker.addListener("click", () => {
            infoWindow.open(map, marker);
        });
    });
}

function getDirectionsTo(placeId) {
    if (!currentLocation) {
        updateStatus("Please set your current location first (use search or detect button).", "error");
        return;
    }

    updateStatus("Calculating directions...");
    
    const travelMode = 'DRIVING';

    directionsService.route({
        origin: new google.maps.LatLng(currentLocation.lat, currentLocation.lng),
        destination: { placeId: placeId },
        travelMode: travelMode
    }, (result, status) => {
        if (status === "OK") {
            directionsRenderer.setDirections(result);
            showRouteInfo(result.routes[0], travelMode);
            updateStatus("Directions shown.");
        } else {
            console.error("Directions request failed:", status);
            updateStatus("Could not get directions to this clinic.", "error");
        }
    });
}

function showRouteInfo(route, travelMode) {
    const leg = route.legs[0];
    new google.maps.InfoWindow({
        content: `
            <div class="route-info">
                <p><i class="fas fa-road"></i> Distance: <strong>${leg.distance.text}</strong></p>
                <p><i class="fas fa-clock"></i> Duration: <strong>${leg.duration.text}</strong></p>
                <p><i class="fas fa-car"></i> Mode: ${travelMode.toLowerCase()}</p>
            </div>
        `,
        position: leg.end_location
    }).open(map);
}

function clearClinics() {
    clinicMarkers.forEach(m => m.setMap(null));
    clinicMarkers = [];
    directionsRenderer.setDirections({ routes: [] });
    document.getElementById("clinics-list").innerHTML = "";
}

function updateStatus(msg, type = "info") {
    const status = document.getElementById("status-text");
    if (status) {
        status.textContent = msg;
        status.className = `status-${type}`;
    }
}

window.initMap = initMap;