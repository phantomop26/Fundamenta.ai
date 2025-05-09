const axios = require('axios');

async function getCoordinatesWithAxios(address, apiKey) {
  try {
    const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${apiKey}`;
    const response = await axios.get(url);
    
    const { results } = response.data;
    
    if (results && results.length > 0) {
      const location = results[0].geometry.location;
      return {
        lat: location.lat,
        lng: location.lng
      };
    } else {
      console.log("No results found");
    }
  } catch (error) {
    console.log("Geocoding failed: " + error.message);
  }
}

const address = "ul";
const API_KEY = "";

getCoordinatesWithAxios(address, API_KEY)
  .then(coordinates => {
    console.log(JSON.stringify(coordinates));
  })
  .catch(error => {
    console.error(error);
  });
