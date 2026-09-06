export interface UserLocationData {
  status: "idle" | "detecting" | "available" | "denied" | "error";
  latitude?: number;
  longitude?: number;
  city?: string;
  district?: string;
  state?: string;
  country?: string;
  formattedAddress?: string;
  displayName: string;
  shortDisplayName: string;
  errorMessage?: string;
}

export async function detectUserLocation(): Promise<UserLocationData> {
  if (typeof window === "undefined" || !navigator.geolocation) {
    return {
      status: "error",
      displayName: "Location unavailable",
      shortDisplayName: "Location",
      errorMessage: "Geolocation not supported by browser",
    };
  }

  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        try {
          const loc = await reverseGeocode(latitude, longitude);
          resolve(loc);
        } catch {
          resolve({
            status: "available",
            latitude,
            longitude,
            displayName: `${latitude.toFixed(2)}°, ${longitude.toFixed(2)}°`,
            shortDisplayName: "Location Set",
          });
        }
      },
      (error) => {
        let msg = "Location unavailable";
        let status: UserLocationData["status"] = "error";

        if (error.code === error.PERMISSION_DENIED) {
          status = "denied";
          msg = "Location permission denied";
        }

        resolve({
          status,
          displayName: "Location unavailable",
          shortDisplayName: "Location",
          errorMessage: msg,
        });
      },
      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 300000, // 5 minutes cache
      }
    );
  });
}

async function reverseGeocode(lat: number, lng: number): Promise<UserLocationData> {
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

  // 1. Try Google Maps Geocoding API if key is provided and not a placeholder
  if (apiKey && apiKey !== "YOUR_GOOGLE_MAPS_API_KEY_HERE") {
    try {
      const url = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lng}&key=${apiKey}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (data.results && data.results.length > 0) {
          const first = data.results[0];
          let city = "";
          let district = "";
          let state = "";
          let country = "";

          for (const comp of first.address_components) {
            if (comp.types.includes("locality") || comp.types.includes("sublocality")) {
              city = comp.long_name;
            }
            if (comp.types.includes("administrative_area_level_2")) {
              district = comp.long_name;
            }
            if (comp.types.includes("administrative_area_level_1")) {
              state = comp.long_name;
            }
            if (comp.types.includes("country")) {
              country = comp.long_name;
            }
          }

          const mainCity = city || district || "Your City";
          const display = state ? `${mainCity}, ${state}` : mainCity;

          return {
            status: "available",
            latitude: lat,
            longitude: lng,
            city,
            district,
            state,
            country,
            formattedAddress: first.formatted_address,
            displayName: display,
            shortDisplayName: mainCity,
          };
        }
      }
    } catch {
      console.warn("Google Maps Geocoding request failed, falling back to OSM...");
    }
  }

  // 2. Fallback: OpenStreetMap Nominatim Reverse Geocoding
  try {
    const osmUrl = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`;
    const res = await fetch(osmUrl, {
      headers: { "Accept-Language": "en" },
    });
    if (res.ok) {
      const data = await res.json();
      const addr = data.address || {};
      const city = addr.suburb || addr.city || addr.town || addr.village || addr.county || "";
      const district = addr.county || addr.state_district || "";
      const state = addr.state || "";
      const country = addr.country || "";

      const mainCity = city || district || "Your Area";
      const display = state ? `${mainCity}, ${state}` : mainCity;

      return {
        status: "available",
        latitude: lat,
        longitude: lng,
        city,
        district,
        state,
        country,
        formattedAddress: data.display_name,
        displayName: display,
        shortDisplayName: mainCity,
      };
    }
  } catch {
    // Ignore fallback failure
  }

  return {
    status: "available",
    latitude: lat,
    longitude: lng,
    displayName: `${lat.toFixed(2)}°, ${lng.toFixed(2)}°`,
    shortDisplayName: "Location Set",
  };
}
