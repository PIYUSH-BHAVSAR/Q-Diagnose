// Quick API test
const BASE = 'https://dung-ununited-seriately.ngrok-free.dev/api';

async function test(endpoint) {
  try {
    const res = await fetch(`${BASE}${endpoint}`, {
      headers: { 'ngrok-skip-browser-warning': 'true' }
    });
    const data = await res.json();
    console.log(`✅ ${endpoint}: ${res.status}`);
    console.log(JSON.stringify(data, null, 2).substring(0, 300));
    return data;
  } catch (e) {
    console.log(`❌ ${endpoint}: ${e.message}`);
  }
}

console.log('Testing experiments endpoints...\n');

// Try different experiment list endpoints
await test('/experiments');
await test('/experiments?limit=10');
await test('/experiment');
await test('/experiments/list');
