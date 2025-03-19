// check whether the browser allows gaining location
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function(position) {
        var lat = position.coords.latitude;
        var lon = position.coords.longitude;

        // use get_weather API
        fetch(`/weather/?lat=${lat}&lon=${lon}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    var weather = data.data;
                    // Concatenate weather information, using default values to prevent missing fields
                    var weatherText = `${weather.name || 'Unknown Location'}: ${weather.temp ?? 'N/A'}°C, ${weather.description || 'No Description'}`;
                    document.getElementById('weather-info').textContent = weatherText;
                } else {
                    document.getElementById('weather-info').textContent = 'Unable to retrieve weather: ' + (data.message || 'Unknown Error');
                }
            })
            .catch(error => {
                console.error('Error fetching weather:', error);
                document.getElementById('weather-info').textContent = 'Weather data loading failed: ' + error.message;
            });
    }, function(error) {
        console.error('Error getting location:', error);
        if (error.code === error.PERMISSION_DENIED) {
            document.getElementById('weather-info').textContent = 'Please allow location access to retrieve weather information';
        } else {
            document.getElementById('weather-info').textContent = 'Unable to retrieve location: ' + error.message;
        }
    });
} else {
    document.getElementById('weather-info').textContent = 'Browser does not support geolocation';
}