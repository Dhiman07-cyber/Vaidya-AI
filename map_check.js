import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Support both ES Modules and CommonJS file paths
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const API_FILE = path.join(__dirname, 'API');

async function getKeys() {
    try {
        if (fs.existsSync(API_FILE)) {
            const content = fs.readFileSync(API_FILE, 'utf8');
            return content.split('\n').map(k => k.trim()).filter(k => k.startsWith('AIza'));
        }
    } catch (e) {
        // Fallback to coded keys if file read fails
    }
    return ["AIzaSyCSTF79ytmSGDQ66OFivGFo1dgG2Pe5DaU"];
}

async function runHealthCheck(key) {
    console.log("\n" + "=".repeat(50));
    console.log(`🔍 DIAGNOSING KEY: ${key}`);
    console.log("=".repeat(50));

    const checks = [
        {
            name: "Geocoding API",
            url: `https://maps.googleapis.com/maps/api/geocode/json?address=New+York&key=${key}`
        },
        {
            name: "Static Maps API",
            url: `https://maps.googleapis.com/maps/api/staticmap?center=0,0&zoom=1&size=100x100&key=${key}`,
            isBinary: true
        },
        {
            name: "Places API (Legacy)",
            url: `https://maps.googleapis.com/maps/api/place/textsearch/json?query=google&key=${key}`
        },
        {
            name: "Places API (New/v2)",
            url: `https://places.googleapis.com/v1/places:searchText`,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': key,
                'X-Goog-FieldMask': 'places.displayName'
            },
            body: JSON.stringify({ textQuery: "Google" })
        },
        {
            name: "Distance Matrix API",
            url: `https://maps.googleapis.com/maps/api/distancematrix/json?origins=Seattle&destinations=Vancouver&key=${key}`
        }
    ];

    let allResults = [];

    for (const check of checks) {
        process.stdout.write(`   Testing ${check.name.padEnd(25)}... `);
        try {
            const options = {
                method: check.method || 'GET',
                headers: check.headers || {}
            };
            if (check.body) options.body = check.body;

            const response = await fetch(check.url, options);

            if (check.isBinary) {
                const contentType = response.headers.get('content-type');
                if (response.ok && contentType && contentType.startsWith('image/')) {
                    console.log("✅ WORKING");
                    allResults.push({ name: check.name, status: "OK" });
                } else {
                    const text = await response.text();
                    console.log("❌ FAILED");
                    interpretError(text);
                }
            } else {
                const data = await response.json();
                if (data.status === "OK" || (data.places && data.places.length > 0) || (response.status === 200 && !data.error)) {
                    console.log("✅ WORKING");
                    allResults.push({ name: check.name, status: "OK" });
                } else {
                    console.log("❌ FAILED");
                    interpretError(JSON.stringify(data));
                }
            }
        } catch (err) {
            console.log("❌ ERROR");
            console.log(`      [System Error]: ${err.message}`);
        }
    }

    const working = allResults.length;
    console.log("-".repeat(50));
    console.log(`   STATUS: ${working}/${checks.length} Services Active`);
    if (working === checks.length) console.log("   🎉 KEY IS FULLY FUNCTIONAL");
    else if (working > 0) console.log("   ⚠️ KEY IS PARTIALLY FUNCTIONAL");
    else console.log("   🚫 KEY IS INACTIVE OR RESTRICTED");
    console.log("-".repeat(50));
}

function interpretError(errorStr) {
    let msg = "Unknown issue";
    if (errorStr.includes("API not activated") || errorStr.includes("ApiNotActivatedMapError")) {
        msg = "Service not enabled in Google Cloud Console.";
    } else if (errorStr.includes("BillingNotEnabled") || errorStr.includes("billing project")) {
        msg = "Billing is not enabled on this project.";
    } else if (errorStr.includes("The provided API key is invalid")) {
        msg = "The API key itself is WRONG/INVALID.";
    } else if (errorStr.includes("KeyRestrictionExceeded") || errorStr.includes("unauthorized")) {
        msg = "IP or Domain restrictions are blocking this request.";
    } else if (errorStr.includes("Legacy API, which is not enabled")) {
        msg = "Calling legacy version; project might be restricted to New v2 APIs.";
    } else {
        try {
            const parsed = JSON.parse(errorStr);
            msg = parsed.error_message || parsed.message || errorStr.slice(0, 80);
        } catch {
            msg = errorStr.slice(0, 80);
        }
    }
    console.log(`      [Issue]: ${msg}`);
}

async function start() {
    const keys = await getKeys();
    console.log("🚀 Starting Google Maps API validation for all keys found...");
    for (const key of keys) {
        await runHealthCheck(key);
    }
}

start();

